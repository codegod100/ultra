from lpython import i32, Const
from ultra import el, end, text, num, cls, cls_if, on_click, button, h1, div, after

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
def step_button(n: i32) -> None:
    el("button")
    cls("chip")
    cls_if("on", step == n)
    on_click(STEP, n)
    text("×")
    num(n)
    end()


def view() -> None:
    div("card")
    h1("Counter")

    el("p")
    cls("count")
    cls_if("neg", count < 0)
    num(count)
    end()

    div("row")
    button("−", DEC, 0)
    button("Reset", RESET, 0)
    button("+", INC, 0)
    end()

    div("row")
    step_button(1)
    step_button(5)
    step_button(10)
    end()

    el("button")
    cls("ghost")
    on_click(TOGGLE_AUTO, 0)
    if auto == 1:
        text("Stop auto")
    else:
        text("Auto-increment")
    end()

    end()
