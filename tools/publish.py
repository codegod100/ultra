#!/usr/bin/env python3
"""Build the ultra conda package (recipe/) and upload it to prefix.dev.

  pixi run publish                       version 0.1.<commit count>, channel nandi-testing
  PREFIX_CHANNEL=other pixi run publish

Auth: PREFIX_API_KEY in the environment, or a one-time
`pixi auth login prefix.dev --token <API key>`. CI does the same in
.github/workflows/conda.yml.
"""

import glob
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(*cmd, **kw):
    print("+", " ".join(cmd), flush=True)
    r = subprocess.run(cmd, cwd=ROOT, **kw)
    if r.returncode:
        sys.exit(r.returncode)
    return r


def main():
    count = run("git", "rev-list", "--count", "HEAD", capture_output=True, text=True).stdout.strip()
    version = os.environ.get("ULTRA_VERSION") or f"0.1.{count}"
    channel = os.environ.get("PREFIX_CHANNEL") or "nandi-testing"
    out = os.path.join(ROOT, "output")
    run("rattler-build", "build", "-r", "recipe/recipe.yaml", "-c", "conda-forge", "--output-dir", out,
        env={**os.environ, "ULTRA_VERSION": version})
    pkgs = glob.glob(os.path.join(out, "noarch", f"ultra-{version}-*.conda"))
    if not pkgs:
        sys.exit(f"no ultra-{version} package in {out}/noarch")
    run("rattler-build", "upload", "prefix", "--skip-existing", "-c", channel, *pkgs)
    print(f"published ultra {version} to https://prefix.dev/channels/{channel}")


if __name__ == "__main__":
    main()
