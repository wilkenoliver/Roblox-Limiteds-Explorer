"""Aba "Comparar": dois itens lado a lado (aceita ID ou nome)."""
from __future__ import annotations

import customtkinter as ctk

from core import api
from core.report import summarize
from core.utils import demand_label, fmt_date, fmt_number, fmt_robux, trend_label

from .theme import run_bg


def _num(v) -> str:
    return fmt_number(v) if v is not None else "—"


def compare_text(full: dict) -> str:
    s = summarize(full)
    return "\n".join([
        f"{s['name']}  (ID {s['id']})",
        f"Tipo: {s['type']}",
        f"Criado em: {fmt_date(s['created'])}",
        f"Limited: {'Sim' if s['is_limited'] else 'Não'}" + (" (U)" if s["is_unique"] else ""),
        "",
        f"Value: {fmt_robux(s['value'])}",
        f"RAP: {fmt_robux(s['rap'])}",
        f"Menor preço: {fmt_robux(s['lowest'])}",
        f"Tendência: {trend_label(s['trend'])}",
        f"Demanda: {demand_label(s['demand'])}",
        f"Projetado: {'Sim' if s['projected'] else 'Não'}",
        "",
        f"Total de cópias: {_num(s['total_copies'])}",
        f"Vendas: {_num(s['sales'])}",
        f"1º registro de revenda: {fmt_date(s['first_record'])}",
    ])


class CompareView(ctk.CTkFrame):
    def __init__(self, master, app) -> None:
        super().__init__(master, fg_color="transparent")
        self.app = app

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=6, pady=6)

        self.e1 = ctk.CTkEntry(top, width=220, placeholder_text="Item A (ID ou nome)")
        self.e1.pack(side="left", padx=4)
        self.e2 = ctk.CTkEntry(top, width=220, placeholder_text="Item B (ID ou nome)")
        self.e2.pack(side="left", padx=4)
        ctk.CTkButton(top, text="Comparar", command=self.compare).pack(side="left", padx=8)
        ctk.CTkButton(top, text="Usar item atual como A", width=170, command=self._use_current).pack(side="left")

        body = ctk.CTkFrame(self)
        body.pack(fill="both", expand=True, padx=6, pady=6)
        body.grid_columnconfigure((0, 1), weight=1)
        body.grid_rowconfigure(0, weight=1)

        self.txt_a = ctk.CTkTextbox(body, wrap="word")
        self.txt_a.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=6)
        self.txt_b = ctk.CTkTextbox(body, wrap="word")
        self.txt_b.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=6)
        for t in (self.txt_a, self.txt_b):
            t.configure(state="disabled")

    def _use_current(self) -> None:
        if self.app.current_item_id:
            self.e1.delete(0, "end")
            self.e1.insert(0, str(self.app.current_item_id))

    def compare(self) -> None:
        a, b = self.e1.get().strip(), self.e2.get().strip()
        if not a or not b:
            return
        self._set(self.txt_a, "Carregando A...")
        self._set(self.txt_b, "Carregando B...")

        def work():
            return self._summary(a), self._summary(b)

        def done(res, err):
            ta, tb = res if res else (f"Erro: {err}", "")
            self._set(self.txt_a, ta)
            self._set(self.txt_b, tb)

        run_bg(self, work, done)

    @staticmethod
    def _summary(text: str) -> str:
        try:
            item_id, _ = api.resolve_item_id(text)
            return compare_text(api.get_full_item(item_id))
        except Exception as e:  # noqa: BLE001
            return f"Erro: {e}"

    @staticmethod
    def _set(widget: ctk.CTkTextbox, text: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.configure(state="disabled")
