from lpython import i32, Const
from ultra import el, end, text, text_ref, num, cls, cls_if, attr, key, on_click, on_enter, div, s_new, s_copy, s_len
from ui import (btn, btn_open, card_open, card_header, card_content_open, card_footer_open,
                input_open, label, badge, badge_num, checkbox, check_field, switch_field,
                tabs_list_open, tab, toggle_group_open, toggle, dialog_open, dialog_footer_open,
                alert, progress, separator, kbd)

# ---- Msg
THEME: Const[i32] = 1
TAB: Const[i32] = 2
NAME: Const[i32] = 3
SAVE: Const[i32] = 4
OPEN: Const[i32] = 5
CLOSE: Const[i32] = 6
CONFIRM: Const[i32] = 7
NOTIFY: Const[i32] = 8
TERMS: Const[i32] = 9
STEP: Const[i32] = 10
ROW: Const[i32] = 11
CLICK: Const[i32] = 12

SYSTEM: Const[i32] = 0
LIGHT: Const[i32] = 1
DARK: Const[i32] = 2

# ---- Model
theme: i32 = 0
tabbed: i32 = 0
name: i32 = 0
saved: i32 = 0
dialog: i32 = 0
deleted: i32 = 0
notify: i32 = 1
terms: i32 = 0
level: i32 = 40
picked: i32 = 0
clicks: i32 = 0


def init() -> None:
    global name
    name = s_new()


# ---- Update
def update(msg: i32, arg: i32) -> None:
    global theme, tabbed, saved, dialog, deleted, notify, terms, level, picked, clicks
    if msg == THEME:
        theme = arg
    elif msg == TAB:
        tabbed = arg
    elif msg == NAME:
        s_copy(name, arg)
        saved = 0
    elif msg == SAVE:
        if s_len(name) > 0:
            saved = 1
    elif msg == OPEN:
        dialog = 1
    elif msg == CLOSE:
        dialog = 0
    elif msg == CONFIRM:
        dialog = 0
        deleted += 1
    elif msg == NOTIFY:
        notify = 1 - notify
    elif msg == TERMS:
        terms = 1 - terms
    elif msg == STEP:
        level += arg
        if level < 0:
            level = 0
        if level > 100:
            level = 100
    elif msg == ROW:
        picked = arg
    elif msg == CLICK:
        clicks += 1


# ---- View
def section(title: str, desc: str) -> None:
    card_open()
    card_header(title, desc)
    card_content_open()


def buttons() -> None:
    section("Button", "Six variants and three sizes.")
    div("row")
    btn("Default", "", CLICK, 0)
    btn("Secondary", "secondary", CLICK, 0)
    btn("Outline", "outline", CLICK, 0)
    btn("Ghost", "ghost", CLICK, 0)
    btn("Destructive", "destructive", CLICK, 0)
    btn("Link", "link", CLICK, 0)
    end()
    el("div")
    cls("row")
    attr("style", "margin-top:.75rem")
    btn_open("outline", CLICK, 0)
    cls("sm")
    text("Small")
    end()
    btn_open("", CLICK, 0)
    cls("lg")
    text("Large")
    end()
    btn_open("outline", CLICK, 0)
    cls("icon")
    attr("aria-label", "Add")
    text("+")
    end()
    el("span")
    cls("muted")
    text("clicked ")
    num(clicks)
    text(" times")
    end()
    end()
    end()
    end()


def badges() -> None:
    section("Badge", "")
    div("row")
    badge("Default", "")
    badge("Secondary", "secondary")
    badge("Destructive", "destructive")
    badge("Outline", "outline")
    badge_num(clicks, "secondary")
    end()
    end()
    end()


def form() -> None:
    card_open()
    card_header("Profile", "Inputs, labels, a checkbox and a switch.")
    card_content_open()
    el("div")
    cls("stack")
    el("div")
    attr("style", "display:grid;gap:.5rem")
    label("Name")
    input_open("Ada Lovelace", name, NAME)
    on_enter(SAVE, 0)
    end()
    end()
    check_field("Accept terms and conditions", terms == 1, TERMS, 0)
    switch_field("Email notifications", notify == 1, NOTIFY, 0)
    if saved == 1:
        el("p")
        cls("muted")
        attr("style", "margin:0")
        text("Saved ")
        text_ref(name)
        text(".")
        end()
    end()
    end()
    card_footer_open()
    btn("Save", "", SAVE, 0)
    el("span")
    cls("muted")
    text("or press ")
    end()
    kbd("Enter")
    end()
    end()


def tabs() -> None:
    section("Tabs", "")
    tabs_list_open()
    tab("Account", tabbed == 0, TAB, 0)
    tab("Password", tabbed == 1, TAB, 1)
    tab("Billing", tabbed == 2, TAB, 2)
    end()
    el("p")
    cls("muted")
    attr("role", "tabpanel")
    if tabbed == 0:
        text("Make changes to your account here.")
    elif tabbed == 1:
        text("Change your password here.")
    else:
        text("Manage your plan and invoices.")
    end()
    end()
    end()


def feedback() -> None:
    section("Alert, Progress, Dialog", "")
    el("div")
    cls("stack")
    alert("Heads up!", "These components are plain CSS plus LPython helpers.", "")
    if deleted > 0:
        alert("Deleted", "Your project was deleted. (Not really.)", "destructive")
    div("row")
    btn("−", "outline", STEP, -10)
    el("div")
    cls("grow")
    progress(level, 100)
    end()
    btn("+", "outline", STEP, 10)
    end()
    separator()
    div("row")
    btn("Delete project", "destructive", OPEN, 0)
    el("span")
    cls("muted")
    text("opens a dialog")
    end()
    end()
    end()
    end()
    end()


def table_row(i: i32, invoice: str, status: str, variant: str, amount: str) -> None:
    el("tr")
    key(i)
    if picked == i:
        attr("aria-selected", "true")
    on_click(ROW, i)
    el("td")
    cls("mono")
    text(invoice)
    end()
    el("td")
    badge(status, variant)
    end()
    el("td")
    attr("style", "text-align:right")
    text(amount)
    end()
    end()


def table() -> None:
    section("Table", "Click a row to select it.")
    el("table")
    cls("table")
    el("thead")
    el("tr")
    el("th")
    text("Invoice")
    end()
    el("th")
    text("Status")
    end()
    el("th")
    attr("style", "text-align:right")
    text("Amount")
    end()
    end()
    end()
    el("tbody")
    table_row(1, "INV001", "Paid", "", "$250.00")
    table_row(2, "INV002", "Pending", "secondary", "$150.00")
    table_row(3, "INV003", "Unpaid", "outline", "$350.00")
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
    badges()
    tabs()
    feedback()
    table()
    end()

    if dialog == 1:
        dialog_open("Are you absolutely sure?",
                    "This action cannot be undone. This will permanently delete your project.", CLOSE)
        dialog_footer_open()
        btn("Cancel", "outline", CLOSE, 0)
        btn("Delete", "destructive", CONFIRM, 0)
        end()
        end()
    end()
