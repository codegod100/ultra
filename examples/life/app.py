# Conway's Game of Life, stepped in wasm and drawn as one DOM element per cell.
# At 150 x 150 that is 22,500 cells diffed and patched every animation frame.
from lpython import i32, Const
from numpy import empty, int32
from ultra import el, end, text, num, cls, cls_if, attr, on_click, frame, div, h1
from ui import btn_open, toggle, toggle_group_open

# ---- Msg
TICK: Const[i32] = 1
PLAY: Const[i32] = 2
STEP: Const[i32] = 3
RANDOM: Const[i32] = 4
CLEAR: Const[i32] = 5
SIZE: Const[i32] = 6        # arg = side length
GUN: Const[i32] = 7

MAXN: Const[i32] = 22500    # 150 * 150

# ---- Model
cells: i32[22500] = empty(22500, dtype=int32)  # 1 alive
nxt: i32[22500] = empty(22500, dtype=int32)
age: i32[22500] = empty(22500, dtype=int32)    # generations alive, for colour
side: i32 = 100
running: i32 = 1
gen: i32 = 0
pop: i32 = 0
seed: i32 = 2463534


def rnd(m: i32) -> i32:
    global seed
    seed = seed ^ (seed << 13)
    seed = seed ^ (seed >> 17)
    seed = seed ^ (seed << 5)
    return (seed & 2147483647) % m


def clear() -> None:
    global gen, pop
    i: i32
    for i in range(side * side):
        cells[i] = 0
        age[i] = 0
    gen = 0
    pop = 0


def randomize() -> None:
    global pop
    i: i32
    clear()
    for i in range(side * side):
        if rnd(100) < 30:
            cells[i] = 1
            age[i] = 1
            pop += 1


def put(x: i32, y: i32) -> None:
    global pop
    i: i32 = y * side + x
    if x < side and y < side and cells[i] == 0:
        cells[i] = 1
        age[i] = 1
        pop += 1


def gun(ox: i32, oy: i32) -> None:
    # Gosper glider gun, 36 x 9
    put(ox + 0, oy + 4)
    put(ox + 0, oy + 5)
    put(ox + 1, oy + 4)
    put(ox + 1, oy + 5)
    put(ox + 10, oy + 4)
    put(ox + 10, oy + 5)
    put(ox + 10, oy + 6)
    put(ox + 11, oy + 3)
    put(ox + 11, oy + 7)
    put(ox + 12, oy + 2)
    put(ox + 12, oy + 8)
    put(ox + 13, oy + 2)
    put(ox + 13, oy + 8)
    put(ox + 14, oy + 5)
    put(ox + 15, oy + 3)
    put(ox + 15, oy + 7)
    put(ox + 16, oy + 4)
    put(ox + 16, oy + 5)
    put(ox + 16, oy + 6)
    put(ox + 17, oy + 5)
    put(ox + 20, oy + 2)
    put(ox + 20, oy + 3)
    put(ox + 20, oy + 4)
    put(ox + 21, oy + 2)
    put(ox + 21, oy + 3)
    put(ox + 21, oy + 4)
    put(ox + 22, oy + 1)
    put(ox + 22, oy + 5)
    put(ox + 24, oy + 0)
    put(ox + 24, oy + 1)
    put(ox + 24, oy + 5)
    put(ox + 24, oy + 6)
    put(ox + 34, oy + 2)
    put(ox + 34, oy + 3)
    put(ox + 35, oy + 2)
    put(ox + 35, oy + 3)


def step() -> None:
    # One generation on a torus.
    global gen, pop
    x: i32
    y: i32
    up: i32
    dn: i32
    lf: i32
    rt: i32
    row: i32
    c: i32
    i: i32
    pop = 0
    for y in range(side):
        up = ((y + side - 1) % side) * side
        row = y * side
        dn = ((y + 1) % side) * side
        for x in range(side):
            lf = (x + side - 1) % side
            rt = (x + 1) % side
            c = (cells[up + lf] + cells[up + x] + cells[up + rt]
                 + cells[row + lf] + cells[row + rt]
                 + cells[dn + lf] + cells[dn + x] + cells[dn + rt])
            i = row + x
            if c == 3 or (c == 2 and cells[i] == 1):
                nxt[i] = 1
            else:
                nxt[i] = 0
    for i in range(side * side):
        cells[i] = nxt[i]
        if cells[i] == 1:
            age[i] += 1
            pop += 1
        else:
            age[i] = 0
    gen += 1


def init() -> None:
    randomize()
    frame(TICK, 0)


# ---- Update
def update(msg: i32, arg: i32) -> None:
    global running, side
    if msg == TICK:
        if running == 1:
            step()
            frame(TICK, 0)
    elif msg == PLAY:
        running = 1 - running
        if running == 1:
            frame(TICK, 0)
    elif msg == STEP:
        step()
    elif msg == RANDOM:
        randomize()
    elif msg == CLEAR:
        clear()
    elif msg == GUN:
        clear()
        gun(2, 2)
        gun(2, side // 2)
    elif msg == SIZE:
        side = arg
        randomize()


# ---- View
def shade(a: i32) -> str:
    if a == 0:
        return ""
    if a == 1:
        return "a1"
    if a < 4:
        return "a2"
    if a < 12:
        return "a3"
    return "a4"


def size_chip(label: str, s: i32) -> None:
    toggle(label, side == s, SIZE, s)


def view() -> None:
    i: i32
    div("card")
    cls("life")
    div("head")
    h1("ultra · Game of Life")
    el("span")
    cls("stats")
    text("gen ")
    num(gen)
    text(" · pop ")
    num(pop)
    text(" · ")
    num(side * side)
    text(" cells")
    end()
    end()

    div("ops")
    btn_open("", PLAY, 0)
    attr("id", "play")
    if running == 1:
        text("Pause")
    else:
        text("Play")
    end()
    btn_open("outline", STEP, 0)
    attr("id", "step")
    text("Step")
    end()
    btn_open("outline", RANDOM, 0)
    text("Random")
    end()
    btn_open("outline", GUN, 0)
    text("Glider guns")
    end()
    btn_open("outline", CLEAR, 0)
    text("Clear")
    end()
    toggle_group_open()
    size_chip("50²", 50)
    size_chip("100²", 100)
    size_chip("150²", 150)
    end()
    end()

    div("grid")
    cls_if("g50", side == 50)
    cls_if("g100", side == 100)
    cls_if("g150", side == 150)
    for i in range(side * side):
        el("i")
        cls(shade(age[i]))
        end()
    end()
    end()
