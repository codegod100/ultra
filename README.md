# ultra

A tiny, Elm-style frontend framework where apps are written in **LPython** and compiled to **WebAssembly**. A ~8 KB (3 KB gzipped) JS glue layer turns your `view()` into DOM patches.

```python
from lpython import i32, Const
from ultra import el, end, num, button, div, h1

INC: Const[i32] = 1          # Msg
DEC: Const[i32] = 2

count: i32 = 0               # Model

def update(msg: i32, arg: i32) -> None:
    global count
    if msg == INC:
        count += 1
    elif msg == DEC:
        count -= 1

def view() -> None:
    div("card")
    h1("Counter")
    el("p"); num(count); end()
    button("−", DEC, 0)
    button("+", INC, 0)
    end()
```

The counter demo compiles to **1.8 KB** of wasm and the todo app to **3.9 KB** (2 KB gzipped).

## The architecture

It's The Elm Architecture, with LPython's types:

| Elm            | ultra                                                       |
| -------------- | ----------------------------------------------------------- |
| `Model`        | typed module-level globals (`count: i32 = 0`, `done: i32[256]`) |
| `Msg`          | `Const[i32]` tags, plus one `i32` payload (`arg`)           |
| `init`         | `def init() -> None` (optional)                             |
| `update`       | `def update(msg: i32, arg: i32) -> None`                    |
| `view`         | `def view() -> None`, which emits a virtual DOM             |
| `Cmd`          | `after(ms, msg, arg)`, localStorage helpers                 |

`view()` describes the UI as a stream of calls: `el("li")`, `cls(...)`, `attr(...)`, `key(...)`, `text(...)`, `num(...)`, `on_click(MSG, arg)`, `end()`. The runtime collects the stream into a vnode tree, diffs it against the previous frame (keyed when you call `key()`), and patches the DOM. Events are delegated from the mount point and become `update(msg, arg)` calls, with re-renders batched onto `requestAnimationFrame`. You never touch the DOM from LPython.

## Quick start

```sh
python3 tools/ultra.py setup                       # fetch LPython 0.22 into .toolchain/ (linux-64)
python3 tools/ultra.py build examples/todo/app.py  # -> examples/todo/app.wasm
python3 tools/ultra.py serve                       # http://localhost:8000/examples/todo/
```

On macOS or Windows, install LPython with `conda install -c conda-forge lpython=0.22` instead of `setup`; `build` uses `lpython` from `PATH` when `.toolchain/` is absent. `setup` needs `pip install zstandard` (or the `zstd` command) to unpack conda packages.

The built `.wasm` files are committed, so `serve` works without the toolchain.

A page mounts an app like this:

```html
<main id="app"></main>
<script type="module">
  import { mount } from "./ultra/ultra.js";
  mount("#app", "./app.wasm");
</script>
```

Browser test (needs Playwright): `python3 tools/ultra.py serve & node tests/e2e.cjs`

## API (`ultra/ultra.py`)

**Elements:** `el(tag)`, `end()`, `text(s)`, `num(i)`, `fnum(x, digits)`, `text_ref(h)`.
Shorthands: `div(cls)`, `span(cls)`, `h1(s)`, `button(label, msg, arg)`, `label_num(s, i)`.

**Attributes:** `attr(name, value)`, `attr_num(name, i)`, `cls(name)`, `cls_if(name, cond)`, `key(i)`, `value_ref(h)`, `checked(cond)`, `autofocus()`.

**Events:** `on_click(msg, arg)`, `on_dblclick(msg, arg)`, `on_enter(msg, arg)`, `on_input(msg)` (sends `update(msg, EVENT)`, with the input's text in string handle `0`).

**Commands:** `after(ms, msg, arg)`, `now_ms()`, `log(i)`.

**Strings:** `s_new()`, `s_dup(h)`, `s_copy(dst, src)`, `s_clear(h)`, `s_free(h)`, `s_len(h)` (trimmed length).

**Storage:** `store_i32(name, v)`, `load_i32(name, default)`, `s_save(name, h)`, `s_load(name, h)`, plus `_at(name, i, ...)` variants for arrays.

## LPython wasm backend limits, and the workarounds

LPython's wasm backend (0.22) is much less complete than its LLVM backend. Here is what we hit and how ultra works around it:

- **No runtime strings.** There is no string concatenation, no f-strings, and no `str(int)`. String literals work. So numbers render through `num()` and `fnum()`, and user-typed text lives in a JS-side store that LPython holds by `i32` handle (`s_new`, `s_dup`, `text_ref`, `value_ref`). Free handles with `s_free` when you drop them.
- **No lists, dicts, or lists of dataclasses.** Use fixed-size `i32` arrays as parallel columns (see `examples/todo/app.py`).
- **Module-level arrays are miscompiled.** `xs: i32[N] = empty(N, dtype=int32)` at module level stores the array's address in a *local* of `__main__global_stmts`, so every global array aliases address 0. `tools/ultra.py build` patches the wasm binary to write those addresses into the right globals. Only `i32` arrays work at module level, because `f64` arrays get an `f64`-typed global. The build tool rejects other array types with a clear error. The patch is tied to LPython 0.22's layout and checks it before applying.
- **Unreachable functions are dropped**, including `update` and `view`, which only JS calls. The build step appends a boot stub that references them behind a condition that is never true, and calls `init()`.
- **JS imports use `@jscall`.** This decorator is undocumented but recognized by the wasm backend: its functions become imports from the `"js"` module. `@ccall` fails with "Function not found".
- **Declare locals at the top of a function.** `h: i32 = ...` inside a loop or branch gives "Variable not declared".
- **Comparisons are `bool`, not `i32`.** `cls_if` and `checked` take `bool`.
- LPython reserves a fixed 64 MB linear memory (1000 pages). Browsers commit it lazily, so this is mostly harmless.

## Layout

```
ultra/ultra.py     LPython API (@jscall declarations + helpers)
ultra/ultra.js     runtime: loader, vnode builder, keyed diff/patch, events, string store
tools/ultra.py     setup / build (with boot stub + wasm patch) / serve
examples/counter   counter with steps and an auto-increment timer
examples/todo      todo list with filters, keyed rows, localStorage persistence
tests/e2e.cjs      Playwright smoke test
```
