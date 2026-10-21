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

The counter example compiles to **3.1 KB** of wasm and the todo app to **5.1 KB** (2.6 KB gzipped), both built with the shadcn-style components below.

## Components (shadcn/ui style)

[shadcn/ui](https://ui.shadcn.com/docs/components) is React + Tailwind + Radix, so it can't run in an ultra app, but its look can. `ultra/ui.css` carries shadcn's neutral theme tokens (`--background`, `--primary`, `--muted-foreground`, `--radius`, …, light and dark) and its component styles as plain CSS, 13 KB (3 KB gzipped). `ultra/ui.py` has view helpers that emit the matching markup and ARIA state:

```python
from ui import btn, card_open, card_header, card_content_open, switch_field

def view() -> None:
    card_open()
    card_header("Counter", "Elm-style state in LPython.")
    card_content_open()
    btn("−", "outline", DEC, 0)
    btn("+", "", INC, 0)
    switch_field("Auto-increment", auto == 1, TOGGLE_AUTO, 0)
    end()
    end()
```

A helper ending in `_open` leaves its element open for children (close it with `end()`); the rest emit a finished element. Variants are shadcn's names passed as a class: `""` (default), `"secondary"`, `"outline"`, `"ghost"`, `"destructive"`, `"link"`.

| Component | Helpers |
| --------- | ------- |
| Button | `btn(label, variant, msg, arg)`, `btn_open(variant, msg, arg)` then `cls("sm" / "lg" / "icon")` |
| Card | `card_open()`, `card_header(title, desc)`, `card_title(s)`, `card_description(s)`, `card_content_open()`, `card_footer_open()` |
| Input, Label | `input_open(placeholder, handle, MSG)` (add `on_enter`, `autofocus`), `label(s)` |
| Badge | `badge(s, variant)`, `badge_num(i, variant)` |
| Checkbox, Switch | `checkbox(on, msg, arg)`, `switch(on, msg, arg)`; with a clickable label: `check_field(s, on, msg, arg)`, `switch_field(...)` |
| Tabs | `tabs_list_open()`, `tab(label, active, msg, arg)` |
| Toggle group | `toggle_group_open()`, `toggle(label, on, msg, arg)`, `toggle_open(on, msg, arg)` |
| Dialog | `dialog_open(title, desc, CLOSE)` (backdrop click, × and Escape send `CLOSE`), `dialog_footer_open()` |
| Alert, Progress, Separator, Kbd | `alert(title, desc, variant)`, `progress(value, max)`, `separator()`, `kbd(s)` |
| Table | plain `el("table")` with `cls("table")`; `aria-selected="true"` on a row highlights it |

Link `ui.css` before your own stylesheet; `build` copies it next to `app.wasm`. Dark mode follows the OS, and `cls("dark")` or `cls("light")` on any element forces it for that subtree. Retheme by overriding the tokens on `:root`. The tokens use CSS `light-dark()`, which needs a 2024-or-later browser. `examples/ui` shows every component, and the other examples are built with them.

## Performance demos

Two examples exist to stress the runtime, and both show their timings on the page:

- **`examples/bench`** is a [js-framework-benchmark](https://github.com/krausest/js-framework-benchmark)-style table: create 1,000 or 10,000 keyed rows, append, update every 10th row, swap two rows, select, remove, clear. The side panel splits each operation into update (wasm), view (wasm building vnodes), diff + DOM patch, and time to next paint. **Run suite** runs the standard set five times and reports medians.
- **`examples/life`** is Conway's Game of Life on a 50², 100² or 150² board, drawn as one DOM element per cell. Each animation frame steps the board in wasm, rebuilds the whole virtual DOM (up to 22,500 cells), diffs it and patches what changed. The panel shows FPS, a frame-time graph, and the per-phase cost.

In headless Chromium on a 4-core cloud VM, ultra's own work (wasm + diff + patch) is about 15 ms for 1,000 rows, 100 ms for 10,000 rows, and 7 ms per frame for the 150² board. The rest of each number is the browser's style, layout and paint. Expect your desktop browser to do much better.

## The architecture

It's The Elm Architecture, with LPython's types:

| Elm            | ultra                                                       |
| -------------- | ----------------------------------------------------------- |
| `Model`        | typed module-level globals (`count: i32 = 0`, `done: i32[256]`) |
| `Msg`          | `Const[i32]` tags, plus one `i32` payload (`arg`)           |
| `init`         | `def init() -> None` (optional)                             |
| `update`       | `def update(msg: i32, arg: i32) -> None`                    |
| `view`         | `def view() -> None`, which emits a virtual DOM             |
| `Cmd`          | `after(ms, msg, arg)`, `frame(msg, arg)`, localStorage helpers |

`view()` describes the UI as a stream of calls: `el("li")`, `cls(...)`, `attr(...)`, `key(...)`, `text(...)`, `num(...)`, `on_click(MSG, arg)`, `end()`. The runtime collects the stream into a vnode tree, diffs it against the previous frame (keyed when you call `key()`), and patches the DOM. Events are delegated from the mount point and become `update(msg, arg)` calls, with re-renders batched onto `requestAnimationFrame`. You never touch the DOM from LPython.

## Quick start

The toolchain (LPython 0.22, Python, Node) is managed with [pixi](https://pixi.sh) from conda-forge, pinned in `pixi.lock`. It works on linux-64, osx-64, osx-arm64, and win-64.

```sh
pixi run build    # compile examples/*/app.py -> app.wasm
pixi run serve    # http://localhost:8000/examples/todo/
```

To build your own app, run `pixi run python tools/ultra.py build path/to/app.py` (it writes `path/to/app.wasm`), or open a shell with the toolchain on `PATH` using `pixi shell`.

Each example folder is self-contained (`index.html`, `app.wasm`, `ultra.js`, `ui.css`, `style.css`), and the built files are committed, so you can run a demo without the toolchain by serving its folder with any static server:

```sh
cd examples/todo && python3 -m http.server     # http://localhost:8000/
```

`build` copies `ultra/ultra.js` and `ultra/ui.css` next to the `.wasm` it writes. A page mounts an app like this:

```html
<main id="app"></main>
<script type="module">
  import { mount } from "./ultra.js";
  mount("#app", "./app.wasm");
</script>
```

Browser test: `pixi run install-playwright` once, then `pixi run test`. It rebuilds the examples, serves the repo on a free port, and runs `tests/e2e.cjs`.

## API (`ultra/ultra.py`)

**Elements:** `el(tag)`, `end()`, `text(s)`, `num(i)`, `fnum(x, digits)`, `text_ref(h)`.
Shorthands: `div(cls)`, `span(cls)`, `h1(s)`, `button(label, msg, arg)`, `label_num(s, i)`.

**Attributes:** `attr(name, value)`, `attr_num(name, i)`, `attr_ref(name, h)`, `cls(name)`, `cls_if(name, cond)`, `key(i)`, `value_ref(h)`, `checked(cond)`, `autofocus()`.

**Events:** `on_click(msg, arg)`, `on_dblclick(msg, arg)`, `on_enter(msg, arg)`, `on_escape(msg, arg)`, `on_input(msg)` (sends `update(msg, EVENT)`, with the input's text in string handle `0`).

**Commands:** `after(ms, msg, arg)`, `frame(msg, arg)` (sends the message at the start of the next animation frame, just before `view()`; call it again from `update()` to run an animation loop), `now_ms()`, `log(i)`.

**Timing hook:** `mount(root, url, { onRender })` calls `onRender({ start, update, view, patch, end, nodes })` after every patch, with times in ms from `performance.now()`. `start` is the first dispatch since the previous render.

**Keyed lists:** call `key(id)` on each child. The diff skips the common prefix and suffix, then moves only the nodes outside the longest increasing subsequence, so swapping two rows of 1,000 moves two DOM nodes. Replacing or clearing a whole list is a single `textContent` reset.

**Strings:** `s_new()`, `s_dup(h)`, `s_copy(dst, src)`, `s_clear(h)`, `s_free(h)`, `s_len(h)` (trimmed length). Build strings at runtime with `s_set(h, "lit")`, `s_add(h, "lit")`, `s_add_ref(h, src)`, `s_add_num(h, i)`; compare with `s_eq(a, b)` and `s_has(h, needle)` (case-insensitive substring).

**HTTP + JSON:** `http_get(url, MSG)` / `http_get_ref(h, MSG)` start a GET and return a JSON handle at once; when the response arrives the runtime calls `update(MSG, handle)`. Check `j_ok(doc)` (or `j_err(doc, h)` for the message), then read by dotted path, with numbers indexing arrays: `j_str(doc, "repos.0.did", h)`, `j_int`, `j_len`, `j_has`. `j_at(doc, path)` and `j_idx(arr, i)` return handles for sub-values (free them with `j_free`), and `j_key(obj, i, h)` reads object keys.

**Your own imports:** declare more `@jscall` functions in your app and pass them to `mount("#app", "./app.wasm", { imports: (ctx) => ({ ... }) })`. `ctx` has `str` (decode an LPython string pointer), `strs` (the string store), `vals` (the JSON store), `text(s)` (emit a text node) and `dispatch(msg, arg)`.

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
ultra/ui.py        shadcn/ui-style component helpers
ultra/ui.css       shadcn theme tokens (light + dark) and component styles
tools/ultra.py     build (with boot stub + wasm patch) / serve / test
pixi.toml          toolchain and tasks (build, serve, test, install-playwright)
examples/counter   counter with steps and an auto-increment timer (self-contained folder)
examples/todo      todo list with filters, keyed rows, localStorage persistence
examples/bench     js-framework-benchmark style keyed table with an in-page timing suite
examples/life      Game of Life animation, up to 22,500 DOM cells per frame, FPS readout
examples/ui        component gallery: buttons, card, form controls, tabs, dialog, table, theme switch
tests/e2e.cjs      Playwright smoke test
```
