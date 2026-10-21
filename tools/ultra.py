#!/usr/bin/env python3
"""ultra build tool.

  python tools/ultra.py build APP.py... [-o OUT.wasm]   (also copies ultra.js, ui.css next to it)
  python tools/ultra.py serve [DIR] [--port 8000]
  python tools/ultra.py test                 serve on a free port, run tests/e2e.cjs

Run it through pixi (`pixi run build`, `pixi run serve`, `pixi run test`),
which provides lpython and node from conda-forge.

The conda package (recipe/) installs this file as the `ultra_tool` module, with
the framework files in ultra_tool/lib, and an `ultra` command for build/serve.

`build` appends a small boot stub to the app so LPython keeps update()/view()
(its wasm backend only emits functions reachable from module-level code) and
runs init() at load time. It also patches around an LPython 0.22 wasm bug
where module-level arrays are allocated into locals instead of globals (see
fix_global_arrays).
"""

import argparse
import http.server
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
# Installed package: ultra_tool/lib. Repo checkout: ultra/ next to tools/.
LIB = os.path.join(HERE, "lib") if os.path.isdir(os.path.join(HERE, "lib")) else os.path.join(ROOT, "ultra")

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
    found = shutil.which("lpython")
    if found:
        return found
    sys.exit("lpython not found. Run this through pixi (`pixi run build`), or put "
             "conda-forge's lpython 0.22 on PATH.")


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


def array_len(name, typ, src):
    """Element count of a module-level `name: i32[N]` (or Array[i32, N]); N is a
    literal or an int constant."""
    m = re.fullmatch(r"(?:i32\[|Array\[\s*i32\s*,)\s*(\w+)\s*\]", typ)
    if m and m.group(1).isdigit():
        return int(m.group(1))
    c = m and re.search(rf"^{m.group(1)}\s*:\s*(?:Const\[i32\]|i32)\s*=\s*(\d+)\s*$", src, re.M)
    if not c:
        sys.exit(f"module-level `{name}: {typ}`: give the size as a number or an i32 "
                 f"constant defined at module level")
    return int(c.group(1))


def pair_regions(addrs, arrays):
    """Name the array that owns each allocation. A region runs to the next higher
    address, so all but the last-placed one have a known size; match those by size."""
    left = list(arrays)
    owner = [None] * len(addrs)
    order = sorted(range(len(addrs)), key=lambda k: addrs[k])
    for a, b in zip(order, order[1:]):
        size = (addrs[b] - addrs[a]) // 4
        fit = [x for x in left if x[1] == size]
        if not fit:
            sys.exit(f"no module-level array has {size} slots (sizes: "
                     f"{sorted(n for _, n in arrays)}); unexpected LPython array layout")
        left.remove(fit[0])
        owner[a] = fit[0][0]
    owner[order[-1]] = left[0][0]
    return owner


def fix_global_arrays(wasm, src):
    """LPython 0.22 compiles `xs: i32[N] = empty(N, dtype=int32)` at module level
    to `i32.const ADDR; local.set k` inside __main__global_stmts, so the global
    that every function reads stays 0 and all arrays alias address 0. Rewrite
    those local.set k into global.set g.

    Module globals follow 7 runtime globals, sorted by name. The allocations
    come in an order of LPython's own (neither source nor name order), packed
    back to back, so each one is paired with an array of the size its region
    has. Arrays of the same size are interchangeable: all start out zeroed."""
    mvars = module_vars(src)
    arrays = [(n, array_len(n, t, src)) for n, t in mvars if re.match(r"(i32\[|Array\[)", t)]
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
    head = i
    allocs = []  # (offset of i32.const, offset after it, address)
    while f[i] == 0x41 and len(allocs) < len(arrays):  # i32.const ADDR ; local.set k
        addr, j = sleb(f, i + 1)
        if f[j] != 0x21:
            break
        _, nxt = uleb(f, j + 1)
        allocs.append((i, j, addr))
        i = nxt
    if len(allocs) != len(arrays):
        sys.exit(f"expected {len(arrays)} array allocations in __main__global_stmts, "
                 f"found {len(allocs)}")
    owner = pair_regions([a for _, _, a in allocs], arrays)
    out = bytearray(f[:head])
    for (s, j, _), name in zip(allocs, owner):
        out += f[s:j] + b"\x24" + enc_uleb(gidx[name])
    out += f[i:]
    bodies[stmts - n_imported] = out

    sec = bytearray(enc_uleb(cnt))
    for fb in bodies:
        sec += enc_uleb(len(fb)) + fb
    return bytes(b[:start]) + b"\x0a" + enc_uleb(len(sec)) + bytes(sec) + bytes(b[end:])


def build(args):
    if args.o and len(args.app) > 1:
        sys.exit("-o needs a single app")
    for app in args.app:
        build_app(app, args.o)


def build_app(path, out=None):
    app = os.path.abspath(path)
    out = os.path.abspath(out or os.path.splitext(app)[0] + ".wasm")
    src = open(app).read()
    has_init = re.search(r"^def\s+init\s*\(", src, re.M) is not None
    for fn in ("update", "view"):
        if not re.search(rf"^def\s+{fn}\s*\(", src, re.M):
            sys.exit(f"{path}: missing `def {fn}(...)`")
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
    # Ship the runtime and stylesheet next to the wasm so the app folder is self-contained and
    # can be served from any directory.
    for f in ("ultra.js", "ui.css"):
        shutil.copy(os.path.join(LIB, f), os.path.join(os.path.dirname(out), f))
    print(f"built {os.path.relpath(out)} ({os.path.getsize(out)} bytes)")


def make_server(directory, port, quiet=False):
    class Handler(http.server.SimpleHTTPRequestHandler):
        extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                          ".wasm": "application/wasm", ".js": "text/javascript"}

        def __init__(self, *a, **kw):
            super().__init__(*a, directory=directory, **kw)

        def log_message(self, *a):
            if not quiet:
                super().log_message(*a)

    return http.server.ThreadingHTTPServer(("", port), Handler)


def serve(args):
    srv = make_server(os.path.abspath(args.dir), args.port)
    print(f"serving {os.path.abspath(args.dir)} on http://localhost:{args.port}")
    srv.serve_forever()


def test(_args):
    srv = make_server(ROOT, 0, quiet=True)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://localhost:{srv.server_address[1]}"
    r = subprocess.run(["node", os.path.join(ROOT, "tests", "e2e.cjs")], cwd=ROOT,
                       env={**os.environ, "BASE": base})
    srv.shutdown()
    sys.exit(r.returncode)


def main():
    p = argparse.ArgumentParser(description="ultra: Elm-style LPython -> wasm frontend")
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("app", nargs="+")
    b.add_argument("-o")
    b.set_defaults(fn=build)
    s = sub.add_parser("serve")
    s.add_argument("dir", nargs="?", default=".")
    s.add_argument("--port", type=int, default=8000)
    s.set_defaults(fn=serve)
    sub.add_parser("test").set_defaults(fn=test)
    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
