"""Aba "Calculadora": lucro de compra/venda com a taxa de 30% do Roblox."""
from __future__ import annotations

import customtkinter as ctk

from core.utils import fmt_robux, profit_calc


class CalculatorView(ctk.CTkFrame):
    def __init__(self, master, app) -> None:
        super().__init__(master, fg_color="transparent")
        self.app = app

        box = ctk.CTkFrame(self)
        box.pack(padx=20, pady=20, fill="x")

        ctk.CTkLabel(box, text="💵 Preço de compra (Robux):").grid(row=0, column=0, sticky="w", padx=8, pady=8)
        self.buy = ctk.CTkEntry(box, width=160)
        self.buy.grid(row=0, column=1, padx=8, pady=8)

        ctk.CTkLabel(box, text="💰 Preço de venda (Robux):").grid(row=1, column=0, sticky="w", padx=8, pady=8)
        self.sell = ctk.CTkEntry(box, width=160)
        self.sell.grid(row=1, column=1, padx=8, pady=8)

        ctk.CTkButton(box, text="Calcular", command=self.calc).grid(row=2, column=0, padx=8, pady=12)

        ctk.CTkLabel(box, text="Preencher com o item atual:").grid(row=3, column=0, sticky="w", padx=8, pady=(8, 0))
        row = ctk.CTkFrame(box, fg_color="transparent")
        row.grid(row=4, column=0, columnspan=2, sticky="w", padx=4, pady=(0, 8))
        for text, key, target in [
            ("Menor preço → compra", "lowest", "buy"),
            ("RAP → venda", "rap", "sell"),
            ("Value → venda", "value", "sell"),
        ]:
            ctk.CTkButton(row, text=text, width=160,
                          command=lambda k=key, t=target: self._fill(k, t)).pack(side="left", padx=4)

        self.out = ctk.CTkTextbox(self, height=200)
        self.out.pack(fill="both", expand=True, padx=20, pady=10)
        self.out.configure(state="disabled")

    def _fill(self, key: str, target: str) -> None:
        s = self.app.current_summary or {}
        v = s.get(key)
        if v is None:
            self._set("O item atual não tem esse valor disponível.")
            return
        entry = self.buy if target == "buy" else self.sell
        entry.delete(0, "end")
        entry.insert(0, str(int(v)))

    def calc(self) -> None:
        try:
            buy = int((self.buy.get() or "0").replace(".", "").strip())
            sell = int((self.sell.get() or "0").replace(".", "").strip())
        except ValueError:
            self._set("Digite números inteiros.")
            return
        r = profit_calc(buy, sell)
        self._set("\n".join([
            f"Compra:               {fmt_robux(r['buy_price'])}",
            f"Venda bruta:          {fmt_robux(r['sell_price'])}",
            f"Taxa Roblox (30%):   -{fmt_robux(r['fee'])}",
            f"Recebido líquido:     {fmt_robux(r['net_received'])}",
            "─" * 34,
            f"Lucro:                {fmt_robux(r['profit'])}",
            f"ROI:                  {r['roi_percent']}%",
            f"Venda mínima p/ não perder: {fmt_robux(r['breakeven_price'])}",
        ]))

    def _set(self, text: str) -> None:
        self.out.configure(state="normal")
        self.out.delete("1.0", "end")
        self.out.insert("1.0", text)
        self.out.configure(state="disabled")
