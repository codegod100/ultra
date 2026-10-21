from lpython import i32, Const
from numpy import empty, int32
from ultra import (el, end, text, text_ref, num, cls, cls_if, attr, key, on_click, on_enter, div,
                   after, s_new, s_set, s_add_num, s_copy, s_len, s_has, store_i32, load_i32)
from ui import (btn, btn_open, card_open, card_header, card_content_open, card_footer_open,
                input_open, label, badge, badge_num, check_field, switch_field,
                tabs_list_open, tab, toggle_group_open, toggle, dialog_open, dialog_footer_open,
                alert, progress, kbd)

# ---- Msg
THEME: Const[i32] = 1
VARIANT: Const[i32] = 2
SIZE: Const[i32] = 3
CLICK: Const[i32] = 4
NAME: Const[i32] = 5
TERMS: Const[i32] = 6
NOTIFY: Const[i32] = 7
SAVE: Const[i32] = 8
UNTOAST: Const[i32] = 9
TAB: Const[i32] = 10
PASSWORD: Const[i32] = 11
PLAN: Const[i32] = 12
SEATS: Const[i32] = 13
STEP: Const[i32] = 14
PLAY: Const[i32] = 15
TICK: Const[i32] = 16
QUERY: Const[i32] = 17
SHOW: Const[i32] = 18
SORT: Const[i32] = 19
PICK: Const[i32] = 20
CYCLE: Const[i32] = 21
OPEN: Const[i32] = 22
CLOSE: Const[i32] = 23
DELETE: Const[i32] = 24
UNDO: Const[i32] = 25

SYSTEM: Const[i32] = 0
LIGHT: Const[i32] = 1
DARK: Const[i32] = 2

ANY: Const[i32] = 3          # status filter: 0 paid, 1 pending, 2 unpaid, 3 any
ROWS: Const[i32] = 6

# ---- Model
theme: i32 = 0
variant: i32 = 0
size: i32 = 1
clicks: i32 = 0

name: i32 = 0                # string handles
terms: i32 = 0
notify: i32 = 1
saves: i32 = 0
toast: i32 = 0               # which save the toast belongs to; 0 = hidden

tabbed: i32 = 0
password: i32 = 0
yearly: i32 = 0
seats: i32 = 3

level: i32 = 30
running: i32 = 0

# Invoices as parallel columns.
inv: i32[6] = empty(6, dtype=int32)        # number, e.g. 3 -> "INV003"
cents: i32[6] = empty(6, dtype=int32)
status: i32[6] = empty(6, dtype=int32)
alive: i32[6] = empty(6, dtype=int32)
labels: i32[6] = empty(6, dtype=int32)     # string handles: "INV003"
methods: i32[6] = empty(6, dtype=int32)    # and "Credit card"
order: i32[6] = empty(6, dtype=int32)      # row indices in display order
query: i32 = 0
show: i32 = 3
sorted_by_amount: i32 = 0
picked: i32 = -1
dialog: i32 = 0
undo: i32 = -1


def add_row(i: i32, c: i32, st: i32, method: str) -> None:
    inv[i] = i + 1
    cents[i] = c
    status[i] = st
    alive[i] = 1
    labels[i] = s_new()
    s_set(labels[i], "INV00")
    s_add_num(labels[i], i + 1)
    methods[i] = s_new()
    s_set(methods[i], method)


def init() -> None:
    global name, password, query, theme
    name = s_new()
    password = s_new()
    query = s_new()
    theme = load_i32("ultra.ui.theme", SYSTEM)
    add_row(0, 25000, 0, "Credit card")
    add_row(1, 15000, 1, "PayPal")
    add_row(2, 35000, 2, "Bank transfer")
    add_row(3, 45000, 0, "Credit card")
    add_row(4, 5000, 0, "PayPal")
    add_row(5, 20000, 1, "Bank transfer")
    reorder()


def reorder() -> None:
    i: i32
    j: i32
    t: i32
    for i in range(ROWS):
        order[i] = i
    if sorted_by_amount == 1:
        for i in range(ROWS):
            for j in range(ROWS - 1 - i):
                if cents[order[j]] < cents[order[j + 1]]:
                    t = order[j]
                    order[j] = order[j + 1]
                    order[j + 1] = t


def can_save() -> bool:
    return s_len(name) > 0 and terms == 1


def price() -> i32:
    if yearly == 1:
        return 120
    return 12


# ---- Update
def update(msg: i32, arg: i32) -> None:
    global theme, variant, size, clicks, terms, notify, saves, toast, tabbed, yearly, seats
    global level, running, show, sorted_by_amount, picked, dialog, undo
    if msg == THEME:
        theme = arg
        store_i32("ultra.ui.theme", theme)
    elif msg == VARIANT:
        variant = arg
    elif msg == SIZE:
        size = arg
    elif msg == CLICK:
        clicks += 1
    elif msg == NAME:
        s_copy(name, arg)
    elif msg == TERMS:
        terms = 1 - terms
    elif msg == NOTIFY:
        notify = 1 - notify
    elif msg == SAVE:
        if can_save():
            saves += 1
            toast = saves
            after(2500, UNTOAST, saves)
    elif msg == UNTOAST:
        if toast == arg:
            toast = 0
    elif msg == TAB:
        tabbed = arg
    elif msg == PASSWORD:
        s_copy(password, arg)
    elif msg == PLAN:
        yearly = arg
    elif msg == SEATS:
        seats += arg
        if seats < 1:
            seats = 1
        if seats > 50:
            seats = 50
    elif msg == STEP:
        level += arg
        if level < 0:
            level = 0
        if level > 100:
            level = 100
    elif msg == PLAY:
        running = 1 - running
        if running == 1:
            if level >= 100:
                level = 0
            after(60, TICK, 0)
    elif msg == TICK:
        if running == 1:
            level += 2
            if level >= 100:
                level = 100
                running = 0
            else:
                after(60, TICK, 0)
    elif msg == QUERY:
        s_copy(query, arg)
    elif msg == SHOW:
        show = arg
    elif msg == SORT:
        sorted_by_amount = 1 - sorted_by_amount
        reorder()
    elif msg == PICK:
        if picked == arg:
            picked = -1
        else:
            picked = arg
    elif msg == CYCLE:
        status[arg] = (status[arg] + 1) % 3
    elif msg == OPEN:
        if picked >= 0:
            dialog = 1
    elif msg == CLOSE:
        dialog = 0
    elif msg == DELETE:
        dialog = 0
        alive[picked] = 0
        undo = picked
        picked = -1
    elif msg == UNDO:
        if undo >= 0:
            alive[undo] = 1
            undo = -1


# ---- View
def variant_name(v: i32) -> str:
    if v == 1:
        return "secondary"
    if v == 2:
        return "outline"
    if v == 3:
        return "ghost"
    if v == 4:
        return "destructive"
    if v == 5:
        return "link"
    return ""


def variant_label(v: i32) -> str:
    if v == 1:
        return "Secondary"
    if v == 2:
        return "Outline"
    if v == 3:
        return "Ghost"
    if v == 4:
        return "Destructive"
    if v == 5:
        return "Link"
    return "Default"


def size_name(s: i32) -> str:
    if s == 0:
        return "sm"
    if s == 2:
        return "lg"
    return ""


def section(title: str, desc: str) -> None:
    card_open()
    card_header(title, desc)
    card_content_open()


def gap() -> None:
    el("div")
    cls("stack")


def money(c: i32) -> None:
    text("$")
    num(c // 100)
    text(".")
    if c % 100 < 10:
        text("0")
    num(c % 100)


def buttons() -> None:
    v: i32
    section("Button", "Pick a variant and size; the preview and the counter update live.")
    gap()
    div("row")
    for v in range(6):
        toggle_like(v)
    end()
    div("row")
    toggle_group_open()
    toggle("Small", size == 0, SIZE, 0)
    toggle("Default", size == 1, SIZE, 1)
    toggle("Large", size == 2, SIZE, 2)
    end()
    end()
    div("preview")
    btn_open(variant_name(variant), CLICK, 0)
    attr("id", "preview")
    cls(size_name(size))
    text(variant_label(variant))
    end()
    el("span")
    cls("muted")
    text("clicked")
    end()
    badge_num(clicks, "secondary")
    end()
    end()
    end()
    end()


def toggle_like(v: i32) -> None:
    btn_open(variant_name(v), VARIANT, v)
    cls("sm")
    cls_if("picked", variant == v)
    text(variant_label(v))
    end()


def form() -> None:
    card_open()
    card_header("Profile", "Save unlocks once there is a name and the terms are accepted.")
    card_content_open()
    gap()

    div("hello")
    el("div")
    cls("hello-name")
    if s_len(name) > 0:
        text_ref(name)
    else:
        text("Anonymous")
    end()
    el("div")
    cls("muted")
    if notify == 1:
        text("Gets email notifications")
    else:
        text("Notifications muted")
    end()
    end()

    el("div")
    cls("field-col")
    div("row")
    label("Name")
    el("span")
    cls("grow")
    end()
    el("span")
    cls("muted")
    num(s_len(name))
    text("/32")
    end()
    end()
    input_open("Ada Lovelace", name, NAME)
    attr("maxlength", "32")
    on_enter(SAVE, 0)
    end()
    end()
    check_field("Accept terms and conditions", terms == 1, TERMS, 0)
    switch_field("Email notifications", notify == 1, NOTIFY, 0)
    if toast > 0:
        el("div")
        cls("alert")
        cls("toast")
        attr("role", "status")
        el("div")
        cls("alert-title")
        text("Saved ")
        text_ref(name)
        text(".")
        end()
        el("div")
        cls("alert-description")
        text("Save #")
        num(saves)
        text(". This message hides itself after 2.5 s.")
        end()
        end()
    end()
    end()

    card_footer_open()
    btn_open("", SAVE, 0)
    attr("id", "save")
    if not can_save():
        attr("disabled", "")
    text("Save")
    end()
    el("span")
    cls("muted")
    text("or press")
    end()
    kbd("Enter")
    end()
    end()


def strength() -> i32:
    n: i32 = s_len(password)
    if n > 10:
        return 100
    return n * 10


def tabs() -> None:
    section("Tabs", "Each tab holds its own live controls.")
    tabs_list_open()
    tab("Account", tabbed == 0, TAB, 0)
    tab("Password", tabbed == 1, TAB, 1)
    tab("Billing", tabbed == 2, TAB, 2)
    end()
    el("div")
    cls("panel")
    attr("role", "tabpanel")
    if tabbed == 0:
        account_tab()
    elif tabbed == 1:
        password_tab()
    else:
        billing_tab()
    end()
    end()
    end()


def account_tab() -> None:
    el("p")
    cls("muted")
    text("Signed in as ")
    if s_len(name) > 0:
        text_ref(name)
    else:
        text("nobody yet (type a name in Profile)")
    text(".")
    end()


def password_tab() -> None:
    s: i32 = strength()
    gap()
    input_open("New password", password, PASSWORD)
    attr("type", "password")
    end()
    div("row")
    el("div")
    cls("grow")
    progress(s, 100)
    end()
    if s == 0:
        badge("Empty", "outline")
    elif s < 50:
        badge("Weak", "destructive")
    elif s < 100:
        badge("Okay", "secondary")
    else:
        badge("Strong", "")
    end()
    end()


def billing_tab() -> None:
    gap()
    div("row")
    toggle_group_open()
    toggle("Monthly", yearly == 0, PLAN, 0)
    toggle("Yearly", yearly == 1, PLAN, 1)
    end()
    if yearly == 1:
        badge("2 months free", "secondary")
    end()
    div("row")
    btn("−", "outline", SEATS, -1)
    el("span")
    cls("seats")
    num(seats)
    text(" seats")
    end()
    btn("+", "outline", SEATS, 1)
    el("span")
    cls("grow")
    end()
    el("span")
    cls("total")
    text("$")
    num(seats * price())
    if yearly == 1:
        text(" / year")
    else:
        text(" / month")
    end()
    end()
    end()


def feedback() -> None:
    section("Alert, Progress", "Play animates the bar with after(); the alert tracks its value.")
    gap()
    if level >= 100:
        alert("Upload complete", "All 100% of the bytes made it.", "")
    elif running == 1:
        alert("Uploading…", "Pause any time.", "")
    else:
        alert("Ready", "Press Play, or nudge the bar by 10%.", "")
    div("row")
    btn("−", "outline", STEP, -10)
    el("div")
    cls("grow")
    progress(level, 100)
    end()
    btn("+", "outline", STEP, 10)
    end()
    div("row")
    btn_open("", PLAY, 0)
    attr("id", "play")
    if running == 1:
        text("Pause")
    else:
        text("Play")
    end()
    badge_num(level, "outline")
    el("span")
    cls("muted")
    text("%")
    end()
    end()
    end()
    end()
    end()


def status_badge(i: i32) -> None:
    el("button")
    cls("badge")
    if status[i] == 0:
        text("Paid")
    elif status[i] == 1:
        cls("secondary")
        text("Pending")
    else:
        cls("outline")
        text("Unpaid")
    attr("title", "Click to change")
    on_click(CYCLE, i)
    end()


def visible(i: i32) -> bool:
    if alive[i] == 0:
        return False
    if show != ANY and status[i] != show:
        return False
    return s_has(labels[i], query) == 1 or s_has(methods[i], query) == 1


def table() -> None:
    k: i32
    i: i32
    shown: i32 = 0
    total: i32 = 0
    for k in range(ROWS):
        if visible(k):
            shown += 1
            total += cents[k]

    section("Table", "Search, filter, sort, click a row to select it, click a status to change it.")
    gap()
    div("row")
    input_open("Search invoices…", query, QUERY)
    cls("grow")
    attr("style", "width:auto")
    end()
    toggle_group_open()
    toggle("All", show == ANY, SHOW, ANY)
    toggle("Paid", show == 0, SHOW, 0)
    toggle("Pending", show == 1, SHOW, 1)
    toggle("Unpaid", show == 2, SHOW, 2)
    end()
    end()

    el("table")
    cls("table")
    el("thead")
    el("tr")
    el("th")
    text("Invoice")
    end()
    el("th")
    text("Method")
    end()
    el("th")
    text("Status")
    end()
    el("th")
    cls("num")
    el("button")
    cls("sort")
    attr("id", "sort")
    on_click(SORT, 0)
    text("Amount")
    if sorted_by_amount == 1:
        text(" ↓")
    else:
        text(" ↕")
    end()
    end()
    end()
    end()
    el("tbody")
    for k in range(ROWS):
        i = order[k]
        if visible(i):
            el("tr")
            key(inv[i])
            if picked == i:
                attr("aria-selected", "true")
            on_click(PICK, i)
            el("td")
            cls("mono")
            text_ref(labels[i])
            end()
            el("td")
            cls("muted")
            text_ref(methods[i])
            end()
            el("td")
            status_badge(i)
            end()
            el("td")
            cls("num")
            money(cents[i])
            end()
            end()
    end()
    el("tfoot")
    el("tr")
    el("td")
    num(shown)
    text(" shown")
    end()
    el("td")
    end()
    el("td")
    end()
    el("td")
    cls("num")
    money(total)
    end()
    end()
    end()
    end()

    div("row")
    btn_open("destructive", OPEN, 0)
    attr("id", "delete")
    if picked < 0:
        attr("disabled", "")
        text("Select a row to delete")
    else:
        text("Delete INV00")
        num(inv[picked])
    end()
    if undo >= 0:
        btn_open("ghost", UNDO, 0)
        text("Undo delete of INV00")
        num(inv[undo])
        end()
    end()
    end()
    end()
    end()


def view() -> None:
    div("page")
    cls_if("light", theme == LIGHT)
    cls_if("dark", theme == DARK)

    div("top")
    el("h1")
    text("ultra/ui")
    end()
    toggle_group_open()
    toggle("System", theme == SYSTEM, THEME, SYSTEM)
    toggle("Light", theme == LIGHT, THEME, LIGHT)
    toggle("Dark", theme == DARK, THEME, DARK)
    end()
    end()

    div("grid")
    buttons()
    form()
    tabs()
    feedback()
    table()
    end()

    if dialog == 1:
        dialog_open("Delete this invoice?",
                    "It disappears from the table. You can undo it afterwards.", CLOSE)
        el("p")
        cls("mono")
        attr("style", "margin:0")
        text_ref(labels[picked])
        text(" · ")
        text_ref(methods[picked])
        text(" · ")
        money(cents[picked])
        end()
        dialog_footer_open()
        btn("Cancel", "outline", CLOSE, 0)
        btn("Delete", "destructive", DELETE, 0)
        end()
        end()
    end()
