#!/usr/bin/env python3
"""ultra build tool.

  python3 tools/ultra.py setup              fetch LPython from conda-forge into .toolchain/
  python3 tools/ultra.py build APP.py [-o OUT.wasm]   (also copies ultra.js next to it)
  python3 tools/ultra.py serve [DIR] [--port 8000]

`build` appends a small boot stub to the app so LPython keeps update()/view()
(its wasm backend only emits functions reachable from module-level code) and
runs init() at load time. It also patches around an LPython 0.22 wasm bug
where module-level arrays are allocated into locals instead of globals (see
fix_global_arrays).
"""

import argparse
import http.server
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(ROOT, "ultra")
TOOLCHAIN = os.path.join(ROOT, ".toolchain")
CHANNEL = "https://conda.anaconda.org/conda-forge/linux-64/"
# lpython plus the two shared libraries its binary links against that aren't
# usually present on a stock Linux (libzmq/libsodium come from the distro).
PACKAGES = [("lpython", "0.22.0"), ("xeus", "5.1"), ("xeus-zmq", "3.0")]

BOOT = """

# ---- ultra boot (generated) ----
from ultra import now_ms as __ultra_now

def __ultra_boot() -> None:
{init}    if __ultra_now() < -1.0:
        update(0, 0)
        view()

__ultra_boot()
"""


def find_lpython():
    local = os.path.join(TOOLCHAIN, "bin", "lpython")
    if os.path.exists(local):
        return local
    found = shutil.which("lpython")
    if found:
        return found
    sys.exit("lpython not found. Run `python3 tools/ultra.py setup`, or install it with "
             "`conda install -c conda-forge lpython`.")


def untar_zst(data, dest):
    try:
        import zstandard
        reader = zstandard.ZstdDecompressor().stream_reader(io.BytesIO(data))
        tarfile.open(fileobj=reader, mode="r|").extractall(dest, filter="fully_trusted")
    except ImportError:
        if not shutil.which("zstd"):
            sys.exit("need `pip install zstandard` or the zstd command to unpack conda packages")
        raw = subprocess.run(["zstd", "-dc"], input=data, capture_output=True, check=True).stdout
        tarfile.open(fileobj=io.BytesIO(raw)).extractall(dest, filter="fully_trusted")


def setup(_args):
    if sys.platform != "linux":
        sys.exit("`setup` downloads linux-64 builds. On macOS/Windows use "
                 "`conda install -c conda-forge lpython`.")
    print("fetching conda-forge index ...")
    repo = json.load(urllib.request.urlopen(CHANNEL + "repodata.json"))
    pkgs = {**repo.get("packages", {}), **repo.get("packages.conda", {})}
    os.makedirs(TOOLCHAIN, exist_ok=True)
    for name, ver in PACKAGES:
        cands = [(v.get("timestamp", 0), f) for f, v in pkgs.items()
                 if v["name"] == name and v["version"].startswith(ver) and f.endswith(".conda")]
        if not cands:
            sys.exit(f"{name} {ver} not found on conda-forge")
        fname = max(cands)[1]
        print("  ", fname)
        z = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(CHANNEL + fname).read()))
        inner = next(n for n in z.namelist() if n.startswith("pkg-"))
        untar_zst(z.read(inner), TOOLCHAIN)
    out = subprocess.run([find_lpython(), "--version"], capture_output=True, text=True)
    print(out.stdout.strip() or out.stderr.strip())


# ---------------------------------------------------------------- wasm patch

def uleb(b, i):
    r = shift = 0
    while True:
        x = b[i]; i += 1
        r |= (x & 0x7f) << shift; shift += 7
        if x < 0x80:
            return r, i


def sleb(b, i):
    r = shift = 0
    while True:
        x = b[i]; i += 1
        r |= (x & 0x7f) << shift; shift += 7
        if x < 0x80:
            if x & 0x40:
                r -= 1 << shift
            return r, i


def enc_uleb(n):
    out = bytearray()
    while True:
        x = n & 0x7f; n >>= 7
        out.append(x | (0x80 if n else 0))
        if not n:
            return bytes(out)


def sections(b):
    i = 8
    while i < len(b):
        sid = b[i]
        size, j = uleb(b, i + 1)
        yield sid, i, j, j + size
        i = j + size


def module_vars(src):
    """Module-level annotated variables of the app, in source order."""
    out = []
    for m in re.finditer(r"^([A-Za-z_]\w*)\s*:\s*([^=\n]+?)\s*(?:=|$)", src, re.M):
        out.append((m.group(1), m.group(2).strip()))
    return out


def fix_global_arrays(wasm, src):
    """LPython 0.22 compiles `xs: i32[N] = empty(N, dtype=int32)` at module level
    to `i32.const ADDR; local.set k` inside __main__global_stmts, so the global
    that every function reads stays 0 and all arrays alias address 0. Rewrite
    those local.set k into global.set g.

    Module globals follow 7 runtime globals, sorted by name; the misplaced
    locals follow source order."""
    mvars = module_vars(src)
    arrays = [n for n, t in mvars if re.match(r"(i32\[|Array\[)", t)]
    for n, t in mvars:
        if re.match(r"[a-z]\w*\[", t) and not t.startswith("i32["):
            sys.exit(f"module-level `{n}: {t}`: only i32 arrays work at module level "
                     f"with LPython's wasm backend")
    if not arrays:
        return wasm
    names = sorted(n for n, _ in mvars)
    gidx = {n: 7 + k for k, n in enumerate(names)}

    b = bytearray(wasm)
    n_imported = 0
    stmts = None
    code = None
    for sid, start, body, end in sections(b):
        if sid == 2:  # imports
            cnt, i = uleb(b, body)
            for _ in range(cnt):
                for _ in range(2):
                    ln, i = uleb(b, i); i += ln
                kind = b[i]; i += 1
                if kind == 0:
                    _, i = uleb(b, i); n_imported += 1
                elif kind == 1:
                    i += 1; fl, i = uleb(b, i); _, i = uleb(b, i)
                    if fl & 1: _, i = uleb(b, i)
                elif kind == 2:
                    fl, i = uleb(b, i); _, i = uleb(b, i)
                    if fl & 1: _, i = uleb(b, i)
                else:
                    i += 2
        elif sid == 6:  # globals: sanity check the layout we assume
            cnt, _ = uleb(b, body)
            if cnt != 7 + len(names):
                sys.exit(f"unexpected global layout ({cnt} globals for {len(names)} module "
                         f"variables); is this LPython 0.22?")
        elif sid == 7:  # exports
            cnt, i = uleb(b, body)
            for _ in range(cnt):
                ln, i = uleb(b, i); nm = bytes(b[i:i + ln]).decode(); i += ln
                kind = b[i]; idx, i = uleb(b, i + 1)
                if kind == 0 and nm == "__main__global_stmts":
                    stmts = idx
        elif sid == 10:
            code = (start, body, end)
    if stmts is None or code is None:
        sys.exit("could not find __main__global_stmts in the wasm output")

    start, body, end = code
    cnt, i = uleb(b, body)
    bodies = []
    for _ in range(cnt):
        sz, j = uleb(b, i)
        bodies.append(bytearray(b[j:j + sz])); i = j + sz
    f = bodies[stmts - n_imported]

    # skip local declarations
    nloc, i = uleb(f, 0)
    for _ in range(nloc):
        _, i = uleb(f, i); i += 1
    out = bytearray(f[:i])
    k = 0
    while f[i] == 0x41:  # i32.const ADDR ; local.set k
        _, j = sleb(f, i + 1)
        if f[j] != 0x21:
            break
        loc, nxt = uleb(f, j + 1)
        if loc >= len(arrays):
            break
        out += f[i:j] + b"\x24" + enc_uleb(gidx[arrays[loc]])
        i = nxt; k += 1
    if k != len(arrays):
        sys.exit(f"expected {len(arrays)} array allocations in __main__global_stmts, found {k}")
    out += f[i:]
    bodies[stmts - n_imported] = out

    sec = bytearray(enc_uleb(cnt))
    for fb in bodies:
        sec += enc_uleb(len(fb)) + fb
    return bytes(b[:start]) + b"\x0a" + enc_uleb(len(sec)) + bytes(sec) + bytes(b[end:])


def build(args):
    app = os.path.abspath(args.app)
    out = os.path.abspath(args.o or os.path.splitext(app)[0] + ".wasm")
    src = open(app).read()
    has_init = re.search(r"^def\s+init\s*\(", src, re.M) is not None
    for fn in ("update", "view"):
        if not re.search(rf"^def\s+{fn}\s*\(", src, re.M):
            sys.exit(f"{args.app}: missing `def {fn}(...)`")
    src += BOOT.format(init="    init()\n" if has_init else "")

    with tempfile.TemporaryDirectory() as tmp:
        main = os.path.join(tmp, os.path.basename(app))
        with open(main, "w") as f:
            f.write(src)
        cmd = [find_lpython(), "--backend=wasm", "-I", LIB, "-I", os.path.dirname(app),
               main, "-o", os.path.join(tmp, "app.wasm")]
        r = subprocess.run(cmd, cwd=tmp)
        if r.returncode != 0:
            sys.exit(r.returncode)
        wasm = open(os.path.join(tmp, "app.wasm"), "rb").read()
        with open(out, "wb") as f:
            f.write(fix_global_arrays(wasm, src))
    # Ship the runtime next to the wasm so the app folder is self-contained and
    # can be served from any directory.
    shutil.copy(os.path.join(LIB, "ultra.js"), os.path.join(os.path.dirname(out), "ultra.js"))
    print(f"built {os.path.relpath(out)} ({os.path.getsize(out)} bytes)")


def serve(args):
    os.chdir(args.dir)
    handler = http.server.SimpleHTTPRequestHandler
    handler.extensions_map[".wasm"] = "application/wasm"
    handler.extensions_map[".js"] = "text/javascript"
    print(f"serving {os.path.abspath(args.dir)} on http://localhost:{args.port}")
    http.server.ThreadingHTTPServer(("", args.port), handler).serve_forever()


def main():
    p = argparse.ArgumentParser(description="ultra: Elm-style LPython -> wasm frontend")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("setup").set_defaults(fn=setup)
    b = sub.add_parser("build")
    b.add_argument("app")
    b.add_argument("-o")
    b.set_defaults(fn=build)
    s = sub.add_parser("serve")
    s.add_argument("dir", nargs="?", default=ROOT)
    s.add_argument("--port", type=int, default=8000)
    s.set_defaults(fn=serve)
    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
