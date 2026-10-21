# ultra.ui: shadcn/ui-style components as view helpers, styled by ui.css.
#
# shadcn/ui itself is React + Tailwind + Radix, so it can't run here. These
# helpers emit the same structure and ARIA state, and ui.css carries its
# theme tokens and component styles.
#
# Naming: a helper ending in _open leaves its element open for children, and
# you close it with end(). Every other helper emits a finished element.
# Variants are class names, as in shadcn: "" (default), "secondary",
# "outline", "ghost", "destructive", "link"; add sizes with cls("sm"),
# cls("lg") or cls("icon") right after btn_open().

from lpython import i32
from ultra import (el, end, text, num, cls, attr, attr_num, value_ref, autofocus,
                   on_click, on_input, on_escape)

# ---------------------------------------------------------------- button

def btn_open(variant: str, msg: i32, arg: i32) -> None:
    el("button")
    cls("btn")
    cls(variant)
    on_click(msg, arg)


def btn(label: str, variant: str, msg: i32, arg: i32) -> None:
    btn_open(variant, msg, arg)
    text(label)
    end()

# ---------------------------------------------------------------- card

def card_open() -> None:
    el("div")
    cls("card")


def card_header(title: str, desc: str) -> None:
    el("div")
    cls("card-header")
    card_title(title)
    if desc != "":
        card_description(desc)
    end()


def card_title(s: str) -> None:
    el("h3")
    cls("card-title")
    text(s)
    end()


def card_description(s: str) -> None:
    el("p")
    cls("card-description")
    text(s)
    end()


def card_content_open() -> None:
    el("div")
    cls("card-content")


def card_footer_open() -> None:
    el("div")
    cls("card-footer")

# ---------------------------------------------------------------- input, label

def input_open(placeholder: str, h: i32, msg: i32) -> None:
    """A text input bound to string handle h; typing sends update(msg, EVENT).
    Add on_enter(), autofocus() or more attributes before end()."""
    el("input")
    cls("input")
    attr("placeholder", placeholder)
    value_ref(h)
    on_input(msg)


def label(s: str) -> None:
    el("label")
    cls("label")
    text(s)
    end()

# ---------------------------------------------------------------- badge

def badge(s: str, variant: str) -> None:
    el("span")
    cls("badge")
    cls(variant)
    text(s)
    end()


def badge_num(x: i32, variant: str) -> None:
    el("span")
    cls("badge")
    cls(variant)
    num(x)
    end()

# ---------------------------------------------------------------- checkbox, switch

def aria(name: str, on: bool) -> None:
    if on:
        attr(name, "true")
    else:
        attr(name, "false")


def checkbox(on: bool, msg: i32, arg: i32) -> None:
    el("button")
    cls("checkbox")
    attr("role", "checkbox")
    aria("aria-checked", on)
    on_click(msg, arg)
    end()


def switch(on: bool, msg: i32, arg: i32) -> None:
    el("button")
    cls("switch")
    attr("role", "switch")
    aria("aria-checked", on)
    on_click(msg, arg)
    end()


def field_open(msg: i32, arg: i32) -> None:
    """A clickable row that holds a control and its label, so clicking the
    text toggles too. check_field() and switch_field() build one for you."""
    el("div")
    cls("field")
    on_click(msg, arg)


def check_field(s: str, on: bool, msg: i32, arg: i32) -> None:
    field_open(msg, arg)
    el("button")
    cls("checkbox")
    attr("role", "checkbox")
    aria("aria-checked", on)
    end()
    label(s)
    end()


def switch_field(s: str, on: bool, msg: i32, arg: i32) -> None:
    field_open(msg, arg)
    el("button")
    cls("switch")
    attr("role", "switch")
    aria("aria-checked", on)
    end()
    label(s)
    end()

# ---------------------------------------------------------------- tabs, toggles

def tabs_list_open() -> None:
    el("div")
    cls("tabs-list")
    attr("role", "tablist")


def tab(s: str, active: bool, msg: i32, arg: i32) -> None:
    el("button")
    cls("tab")
    attr("role", "tab")
    aria("aria-selected", active)
    on_click(msg, arg)
    text(s)
    end()


def toggle_group_open() -> None:
    el("div")
    cls("toggle-group")
    attr("role", "group")


def toggle_open(on: bool, msg: i32, arg: i32) -> None:
    el("button")
    cls("toggle")
    aria("aria-pressed", on)
    on_click(msg, arg)


def toggle(s: str, on: bool, msg: i32, arg: i32) -> None:
    toggle_open(on, msg, arg)
    text(s)
    end()

# ---------------------------------------------------------------- dialog

def dialog_open(title: str, desc: str, close: i32) -> None:
    """A modal: backdrop, panel, header and a close button. Clicking the
    backdrop, the close button or pressing Escape sends update(close, 0).
    Only call it while the dialog is shown, and close the panel with end()."""
    el("div")
    cls("dialog-overlay")
    on_click(close, 0)
    end()
    el("div")
    cls("dialog")
    attr("role", "dialog")
    attr("aria-modal", "true")
    attr_num("tabindex", -1)
    autofocus()
    on_escape(close, 0)
    el("div")
    cls("dialog-header")
    el("h2")
    cls("dialog-title")
    text(title)
    end()
    if desc != "":
        el("p")
        cls("dialog-description")
        text(desc)
        end()
    end()
    el("button")
    cls("dialog-close")
    attr("aria-label", "Close")
    on_click(close, 0)
    text("×")
    end()


def dialog_footer_open() -> None:
    el("div")
    cls("dialog-footer")

# ---------------------------------------------------------------- feedback

def alert(title: str, desc: str, variant: str) -> None:
    el("div")
    cls("alert")
    cls(variant)
    attr("role", "alert")
    el("div")
    cls("alert-title")
    text(title)
    end()
    if desc != "":
        el("div")
        cls("alert-description")
        text(desc)
        end()
    end()


def progress(value: i32, total: i32) -> None:
    el("progress")
    cls("progress")
    attr_num("value", value)
    attr_num("max", total)
    end()


def separator() -> None:
    el("hr")
    cls("separator")
    end()


def kbd(s: str) -> None:
    el("kbd")
    cls("kbd")
    text(s)
    end()
