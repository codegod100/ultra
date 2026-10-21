"""Regression test: module-level arrays of different sizes must not overlap.

Builds tests/arrays/app.py with tools/ultra.py (or the installed `ultra` command
when tools/ is absent, as in the conda package test), runs it under Node with
stub imports, and checks that every array kept the tags update() wrote into it.
Needs lpython 0.22 and node on PATH:  pixi run test-arrays
"""

import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.join(os.path.dirname(HERE), "tools", "ultra.py")

RUN = r"""
const fs = require("fs");
const mod = new WebAssembly.Module(fs.readFileSync(process.argv[1]));
const out = [];
const imports = {};
for (const imp of WebAssembly.Module.imports(mod)) {
  imports[imp.module] ??= {};
  imports[imp.module][imp.name] = imp.name === "num" ? (x) => out.push(x)
                                : imp.name === "now_ms" ? () => 0 : () => 0;
}
const { exports: e } = new WebAssembly.Instance(mod, imports);
e.__main__global_stmts();
e.update(0, 0);
e.view();
console.log(JSON.stringify(out));
"""


def main():
    with tempfile.TemporaryDirectory() as tmp:
        wasm = os.path.join(tmp, "app.wasm")
        ultra = [sys.executable, TOOL] if os.path.exists(TOOL) else ["ultra"]
        subprocess.run(ultra + ["build", os.path.join(HERE, "arrays", "app.py"),
                        "-o", wasm], check=True, stdout=subprocess.DEVNULL)
        r = subprocess.run(["node", "-e", RUN, wasm], check=True, capture_output=True, text=True)
    bad = r.stdout.strip()
    if bad != "[0]":
        sys.exit(f"arrays: expected [0] overwritten slots, view() reported {bad}")
    print("arrays ok")


if __name__ == "__main__":
    main()
