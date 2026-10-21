from lpython import i32, Const
from ultra import el, end, text, num, cls, cls_if, after, div
from ui import (btn, card_open, card_header, card_content_open, card_footer_open,
                toggle_group_open, toggle_open, switch_field)

# ---- Msg
INC: Const[i32] = 1
DEC: Const[i32] = 2
RESET: Const[i32] = 3
STEP: Const[i32] = 4
TOGGLE_AUTO: Const[i32] = 5
TICK: Const[i32] = 6

# ---- Model
count: i32 = 0
step: i32 = 1
auto: i32 = 0


# ---- Update
def update(msg: i32, arg: i32) -> None:
    global count, step, auto
    if msg == INC:
        count += step
    elif msg == DEC:
        count -= step
    elif msg == RESET:
        count = 0
    elif msg == STEP:
        step = arg
    elif msg == TOGGLE_AUTO:
        auto = 1 - auto
        if auto == 1:
            after(500, TICK, 0)
    elif msg == TICK:
        if auto == 1:
            count += step
            after(500, TICK, 0)


# ---- View
def step_toggle(n: i32) -> None:
    toggle_open(step == n, STEP, n)
    text("×")
    num(n)
    end()


def view() -> None:
    card_open()
    card_header("Counter", "Elm-style state in LPython, compiled to wasm.")

    card_content_open()
    el("p")
    cls("count")
    cls_if("neg", count < 0)
    num(count)
    end()
    div("row")
    btn("−", "outline", DEC, 0)
    btn("Reset", "secondary", RESET, 0)
    btn("+", "", INC, 0)
    end()
    end()

    card_footer_open()
    toggle_group_open()
    step_toggle(1)
    step_toggle(5)
    step_toggle(10)
    end()
    switch_field("Auto-increment", auto == 1, TOGGLE_AUTO, 0)
    end()

    end()
