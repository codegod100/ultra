# js-framework-benchmark style table: create, update, swap, select and remove
# thousands of keyed rows. The page around the app times every operation.
from lpython import i32, Const
from numpy import empty, int32
from ultra import el, end, text, num, cls, cls_if, attr, key, on_click, div, h1
from ui import btn_open

# ---- Msg
RUN: Const[i32] = 1         # replace all rows with arg new ones
ADD: Const[i32] = 2         # append arg rows
UPDATE: Const[i32] = 3      # append " !!!" to every 10th row
CLEAR: Const[i32] = 4
SWAP: Const[i32] = 5        # swap rows 1 and 998
SELECT: Const[i32] = 6      # arg = row id
REMOVE: Const[i32] = 7      # arg = row id

CAP: Const[i32] = 20000

# ---- Model: one row per index, as parallel columns
ids: i32[20000] = empty(20000, dtype=int32)
adj: i32[20000] = empty(20000, dtype=int32)
col: i32[20000] = empty(20000, dtype=int32)
noun: i32[20000] = empty(20000, dtype=int32)
bang: i32[20000] = empty(20000, dtype=int32)   # how many " !!!" to show
n: i32 = 0
next_id: i32 = 1
selected: i32 = 0
seed: i32 = 42


def rnd(m: i32) -> i32:
    global seed
    seed = seed ^ (seed << 13)
    seed = seed ^ (seed >> 17)
    seed = seed ^ (seed << 5)
    return (seed & 2147483647) % m


def adjective(k: i32) -> str:
    if k == 0:
        return "pretty "
    if k == 1:
        return "large "
    if k == 2:
        return "big "
    if k == 3:
        return "small "
    if k == 4:
        return "tall "
    if k == 5:
        return "short "
    if k == 6:
        return "long "
    if k == 7:
        return "handsome "
    if k == 8:
        return "plain "
    if k == 9:
        return "quaint "
    if k == 10:
        return "clean "
    if k == 11:
        return "elegant "
    if k == 12:
        return "easy "
    if k == 13:
        return "angry "
    if k == 14:
        return "crazy "
    if k == 15:
        return "helpful "
    if k == 16:
        return "mushy "
    if k == 17:
        return "odd "
    if k == 18:
        return "unsightly "
    if k == 19:
        return "adorable "
    if k == 20:
        return "important "
    if k == 21:
        return "inexpensive "
    if k == 22:
        return "cheap "
    if k == 23:
        return "expensive "
    return "fancy "


def colour(k: i32) -> str:
    if k == 0:
        return "red "
    if k == 1:
        return "yellow "
    if k == 2:
        return "blue "
    if k == 3:
        return "green "
    if k == 4:
        return "pink "
    if k == 5:
        return "brown "
    if k == 6:
        return "purple "
    if k == 7:
        return "brown "
    if k == 8:
        return "white "
    if k == 9:
        return "black "
    return "orange "


def thing(k: i32) -> str:
    if k == 0:
        return "table"
    if k == 1:
        return "chair"
    if k == 2:
        return "house"
    if k == 3:
        return "bbq"
    if k == 4:
        return "desk"
    if k == 5:
        return "car"
    if k == 6:
        return "pony"
    if k == 7:
        return "cookie"
    if k == 8:
        return "sandwich"
    if k == 9:
        return "burger"
    if k == 10:
        return "pizza"
    if k == 11:
        return "mouse"
    return "keyboard"


def add_rows(count: i32) -> None:
    global n, next_id
    i: i32
    for i in range(count):
        if n < CAP:
            ids[n] = next_id
            adj[n] = rnd(25)
            col[n] = rnd(11)
            noun[n] = rnd(13)
            bang[n] = 0
            next_id += 1
            n += 1


def find(id: i32) -> i32:
    i: i32
    for i in range(n):
        if ids[i] == id:
            return i
    return -1


def swap(a: i32, b: i32) -> None:
    t: i32
    t = ids[a]
    ids[a] = ids[b]
    ids[b] = t
    t = adj[a]
    adj[a] = adj[b]
    adj[b] = t
    t = col[a]
    col[a] = col[b]
    col[b] = t
    t = noun[a]
    noun[a] = noun[b]
    noun[b] = t
    t = bang[a]
    bang[a] = bang[b]
    bang[b] = t


# ---- Update
def update(msg: i32, arg: i32) -> None:
    global n, selected
    i: i32
    at: i32
    if msg == RUN:
        n = 0
        selected = 0
        add_rows(arg)
    elif msg == ADD:
        add_rows(arg)
    elif msg == UPDATE:
        i = 0
        while i < n:
            bang[i] += 1
            i += 10
    elif msg == CLEAR:
        n = 0
        selected = 0
    elif msg == SWAP:
        if n > 998:
            swap(1, 998)
    elif msg == SELECT:
        selected = arg
    elif msg == REMOVE:
        at = find(arg)
        if at >= 0:
            for i in range(at, n - 1):
                ids[i] = ids[i + 1]
                adj[i] = adj[i + 1]
                col[i] = col[i + 1]
                noun[i] = noun[i + 1]
                bang[i] = bang[i + 1]
            n -= 1


# ---- View
def op(id: str, label: str, variant: str, msg: i32, arg: i32) -> None:
    btn_open(variant, msg, arg)
    attr("id", id)
    text(label)
    end()


def view_row(i: i32) -> None:
    b: i32
    el("tr")
    key(ids[i])
    cls_if("danger", ids[i] == selected)

    el("td")
    cls("id")
    num(ids[i])
    end()

    el("td")
    cls("lbl")
    el("a")
    on_click(SELECT, ids[i])
    text(adjective(adj[i]))
    text(colour(col[i]))
    text(thing(noun[i]))
    for b in range(bang[i]):
        text(" !!!")
    end()
    end()

    el("td")
    el("a")
    cls("x")
    attr("aria-label", "Remove")
    on_click(REMOVE, ids[i])
    text("×")
    end()
    end()

    end()


def view() -> None:
    i: i32
    div("card")
    cls("bench")
    div("head")
    h1("ultra · keyed rows")
    el("span")
    cls("badge")
    cls("secondary")
    cls("rows")
    num(n)
    text(" rows")
    end()
    end()

    div("ops")
    op("run", "Create 1,000", "", RUN, 1000)
    op("runlots", "Create 10,000", "outline", RUN, 10000)
    op("add", "Append 1,000", "outline", ADD, 1000)
    op("update", "Update every 10th", "outline", UPDATE, 0)
    op("swaprows", "Swap rows", "outline", SWAP, 0)
    op("clear", "Clear", "outline", CLEAR, 0)
    end()

    el("table")
    cls("table")
    el("tbody")
    for i in range(n):
        view_row(i)
    end()
    end()
    end()
