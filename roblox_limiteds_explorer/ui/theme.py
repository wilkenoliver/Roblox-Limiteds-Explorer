"""Helpers de interface: threads seguras, estilo da tabela, cores."""
from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable

import customtkinter as ctk


def safe_after(widget: Any, fn: Callable[[], None]) -> None:
    """Agenda `fn` na thread da interface; ignora se a janela já fechou."""
    try:
        widget.after(0, fn)
    except Exception:
        pass


def run_bg(widget: Any, work: Callable[[], Any], done: Callable[[Any, str | None], None]) -> None:
    """Roda `work()` em thread e chama `done(resultado, erro)` na interface."""
    def target() -> None:
        try:
            res, err = work(), None
        except Exception as e:  # noqa: BLE001
            res, err = None, (str(e) or e.__class__.__name__)
        safe_after(widget, lambda: done(res, err))

    threading.Thread(target=target, daemon=True).start()


def is_dark() -> bool:
    return ctk.get_appearance_mode() == "Dark"


def _pick(color: Any) -> str:
    if isinstance(color, (list, tuple)):
        return color[1] if is_dark() else color[0]
    return color


def apply_treeview_style() -> None:
    """Deixa o ttk.Treeview com as cores do tema atual (claro/escuro)."""
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    th = ctk.ThemeManager.theme
    bg = _pick(th["CTkFrame"]["fg_color"])
    head = _pick(th["CTkFrame"]["top_fg_color"])
    fg = _pick(th["CTkLabel"]["text_color"])
    sel = _pick(th["CTkButton"]["fg_color"])

    style.configure("Treeview", background=bg, fieldbackground=bg, foreground=fg,
                    rowheight=26, borderwidth=0)
    style.map("Treeview", background=[("selected", sel)], foreground=[("selected", "white")])
    style.configure("Treeview.Heading", background=head, foreground=fg, relief="flat",
                    font=("Segoe UI", 10, "bold"))
    style.map("Treeview.Heading", background=[("active", sel)])


def chart_colors() -> tuple[str, str, str]:
    """(fundo, texto, grade) para o matplotlib."""
    if is_dark():
        return "#2b2b2b", "#e5e5e5", "#555555"
    return "#ebebeb", "#1a1a1a", "#bbbbbb"
