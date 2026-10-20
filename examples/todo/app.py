from lpython import i32, Const
from numpy import empty, int32
from ultra import (el, end, text, text_ref, num, cls, cls_if, attr, key, value_ref,
                   checked, autofocus, on_click, on_input, on_enter, div, h1,
                   s_new, s_dup, s_copy, s_clear, s_free, s_len, s_save_at, s_load_at,
                   store_i32, load_i32, store_i32_at, load_i32_at)

# ---- Msg
INPUT: Const[i32] = 1
ADD: Const[i32] = 2
TOGGLE: Const[i32] = 3
DELETE: Const[i32] = 4
FILTER: Const[i32] = 5
CLEAR_DONE: Const[i32] = 6
TOGGLE_ALL: Const[i32] = 7

ALL: Const[i32] = 0
ACTIVE: Const[i32] = 1
DONE: Const[i32] = 2

CAP: Const[i32] = 256

# ---- Model
# Parallel arrays (LPython's wasm backend has no lists of structs yet).
texts: i32[256] = empty(256, dtype=int32)   # string handles
done: i32[256] = empty(256, dtype=int32)
ids: i32[256] = empty(256, dtype=int32)
n: i32 = 0
next_id: i32 = 1
draft: i32 = 0
show: i32 = 0


def init() -> None:
    global draft, n, next_id, show
    draft = s_new()
    # restore from localStorage
    count: i32 = load_i32("ultra.todo.n", 0)
    i: i32
    h: i32
    for i in range(count):
        h = s_new()
        if s_load_at("ultra.todo.text", i, h) == 1 and n < CAP:
            texts[n] = h
            done[n] = load_i32_at("ultra.todo.done", i, 0)
            ids[n] = next_id
            next_id += 1
            n += 1
        else:
            s_free(h)
    show = load_i32("ultra.todo.show", ALL)


def save() -> None:
    i: i32
    store_i32("ultra.todo.n", n)
    store_i32("ultra.todo.show", show)
    for i in range(n):
        s_save_at("ultra.todo.text", i, texts[i])
        store_i32_at("ultra.todo.done", i, done[i])


def remaining() -> i32:
    r: i32 = 0
    i: i32
    for i in range(n):
        if done[i] == 0:
            r += 1
    return r


def remove_at(at: i32) -> None:
    global n
    s_free(texts[at])
    j: i32
    for j in range(at, n - 1):
        texts[j] = texts[j + 1]
        done[j] = done[j + 1]
        ids[j] = ids[j + 1]
    n -= 1


# ---- Update
def update(msg: i32, arg: i32) -> None:
    global n, next_id, show
    i: i32
    v: i32
    if msg == INPUT:
        s_copy(draft, arg)
    elif msg == ADD:
        if s_len(draft) > 0 and n < CAP:
            texts[n] = s_dup(draft)
            done[n] = 0
            ids[n] = next_id
            next_id += 1
            n += 1
            s_clear(draft)
    elif msg == TOGGLE:
        done[arg] = 1 - done[arg]
    elif msg == DELETE:
        remove_at(arg)
    elif msg == FILTER:
        show = arg
    elif msg == CLEAR_DONE:
        i = n - 1
        while i >= 0:
            if done[i] == 1:
                remove_at(i)
            i -= 1
    elif msg == TOGGLE_ALL:
        v = 0
        if remaining() > 0:
            v = 1
        for i in range(n):
            done[i] = v
    if msg != INPUT:
        save()


# ---- View
def filter_link(label: str, which: i32) -> None:
    el("button")
    cls("chip")
    cls_if("on", show == which)
    on_click(FILTER, which)
    text(label)
    end()


def visible(i: i32) -> bool:
    if show == ACTIVE:
        return done[i] == 0
    if show == DONE:
        return done[i] == 1
    return True


def view_item(i: i32) -> None:
    el("li")
    key(ids[i])
    cls("item")
    cls_if("done", done[i] == 1)

    el("input")
    attr("type", "checkbox")
    checked(done[i] == 1)
    on_click(TOGGLE, i)
    end()

    el("label")
    text_ref(texts[i])
    end()

    el("button")
    cls("x")
    attr("aria-label", "Delete")
    on_click(DELETE, i)
    text("×")
    end()

    end()


def view() -> None:
    i: i32
    div("card")
    h1("Todos")

    div("row")
    el("input")
    cls("new")
    attr("placeholder", "What needs doing?")
    value_ref(draft)
    autofocus()
    on_input(INPUT)
    on_enter(ADD, 0)
    end()
    el("button")
    on_click(ADD, 0)
    text("Add")
    end()
    end()

    el("ul")
    cls("list")
    for i in range(n):
        if visible(i):
            view_item(i)
    end()

    if n > 0:
        div("footer")
        el("span")
        num(remaining())
        text(" left")
        end()
        div("row")
        filter_link("All", ALL)
        filter_link("Active", ACTIVE)
        filter_link("Done", DONE)
        end()
        el("button")
        cls("ghost")
        on_click(CLEAR_DONE, 0)
        text("Clear done")
        end()
        end()

    end()
