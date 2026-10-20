# ultra: an Elm-style UI framework for LPython -> WebAssembly.
#
# An app defines three things:
#   init()                    set up the model (optional)
#   update(msg: i32, arg: i32) handle a message, mutate the model
#   view()                    describe the UI from the model
#
# view() emits a virtual DOM as a stream of calls (el / attr / text / end).
# The JS runtime (ultra.js) collects them into a tree, diffs it against the
# previous one and patches the real DOM. Events are messages: on_click(MSG, arg)
# makes the runtime call update(MSG, arg) and re-render on the next frame.
#
# Everything decorated with @jscall is imported from the "js" module that
# ultra.js provides.

from lpython import i32, f64

# ---------------------------------------------------------------- elements

@jscall
def el(tag: str) -> None:
    """Open an element. Must be closed with end()."""
    pass

@jscall
def end() -> None:
    pass

@jscall
def text(s: str) -> None:
    pass

@jscall
def num(x: i32) -> None:
    """Text node with an integer."""
    pass

@jscall
def fnum(x: f64, digits: i32) -> None:
    """Text node with a float, fixed number of digits."""
    pass

@jscall
def text_ref(h: i32) -> None:
    """Text node with a runtime string (see the string store below)."""
    pass

# ---------------------------------------------------------------- attributes

@jscall
def attr(name: str, value: str) -> None:
    pass

@jscall
def attr_num(name: str, value: i32) -> None:
    pass

@jscall
def cls(name: str) -> None:
    """Add a CSS class. May be called several times."""
    pass

@jscall
def cls_if(name: str, on: bool) -> None:
    pass

@jscall
def key(k: i32) -> None:
    """Stable identity for a child in a list, so reorders patch cleanly."""
    pass

@jscall
def value_ref(h: i32) -> None:
    """Bind an <input>'s value to a runtime string."""
    pass

@jscall
def checked(on: bool) -> None:
    pass

@jscall
def autofocus() -> None:
    pass

# ---------------------------------------------------------------- events

@jscall
def on_click(msg: i32, arg: i32) -> None:
    pass

@jscall
def on_input(msg: i32) -> None:
    """update(msg, EVENT) on every keystroke; read the text via handle EVENT."""
    pass

@jscall
def on_enter(msg: i32, arg: i32) -> None:
    """update(msg, arg) when Enter is pressed."""
    pass

@jscall
def on_dblclick(msg: i32, arg: i32) -> None:
    pass

# ---------------------------------------------------------------- commands

@jscall
def after(ms: i32, msg: i32, arg: i32) -> None:
    """Send update(msg, arg) once after ms milliseconds (like Elm's Process.sleep)."""
    pass

@jscall
def frame(msg: i32, arg: i32) -> None:
    """Send update(msg, arg) at the start of the next animation frame, just
    before view(). Call it again from update() to run an animation loop."""
    pass

@jscall
def now_ms() -> f64:
    pass

@jscall
def log(x: i32) -> None:
    pass

# ---------------------------------------------------------------- strings
#
# LPython's wasm backend can't build strings at runtime yet, so text the user
# types lives in a JS-side store and LPython holds integer handles.
# Handle 0 (EVENT) is the scratch slot that on_input() writes to.

@jscall
def s_new() -> i32:
    pass

@jscall
def s_dup(h: i32) -> i32:
    pass

@jscall
def s_copy(dst: i32, src: i32) -> None:
    pass

@jscall
def s_clear(h: i32) -> None:
    pass

@jscall
def s_free(h: i32) -> None:
    pass

@jscall
def s_len(h: i32) -> i32:
    """Length after trimming whitespace."""
    pass

@jscall
def s_save(name: str, h: i32) -> None:
    """Persist a string handle in localStorage."""
    pass

@jscall
def s_load(name: str, h: i32) -> i32:
    """Load localStorage[name] into h. Returns 1 if found."""
    pass

@jscall
def store_i32(name: str, v: i32) -> None:
    pass

@jscall
def load_i32(name: str, default: i32) -> i32:
    pass

# Indexed variants use the key "name.i", for saving arrays.

@jscall
def s_save_at(name: str, i: i32, h: i32) -> None:
    pass

@jscall
def s_load_at(name: str, i: i32, h: i32) -> i32:
    pass

@jscall
def store_i32_at(name: str, i: i32, v: i32) -> None:
    pass

@jscall
def load_i32_at(name: str, i: i32, default: i32) -> i32:
    pass

# ---------------------------------------------------------------- shorthands

def div(c: str) -> None:
    el("div")
    cls(c)

def span(c: str) -> None:
    el("span")
    cls(c)

def button(label: str, msg: i32, arg: i32) -> None:
    el("button")
    on_click(msg, arg)
    text(label)
    end()

def h1(s: str) -> None:
    el("h1")
    text(s)
    end()

def label_num(s: str, x: i32) -> None:
    el("span")
    text(s)
    num(x)
    end()
