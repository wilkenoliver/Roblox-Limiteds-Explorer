"""Aba "Histórico": preço médio (RAP) real ao longo do tempo."""
from __future__ import annotations

import threading

import customtkinter as ctk
import matplotlib

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402

from core import api  # noqa: E402

from .theme import chart_colors, safe_after  # noqa: E402


class ChartView(ctk.CTkFrame):
    def __init__(self, master, app) -> None:
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.item_id: int | None = None
        self.points: list[dict] = []
        self.value: int | None = None
        self.name = ""

        self.label = ctk.CTkLabel(self, text="Busque um item para ver o histórico.")
        self.label.pack(pady=6)

        self.fig = Figure(figsize=(10, 4.6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)
        self._redraw()

    # ------------------------------------------------------------------
    def load_item(self, item_id: int) -> None:
        self.item_id = item_id
        self.label.configure(text=f"Carregando histórico do item {item_id}...")
        threading.Thread(target=self._worker, args=(item_id,), daemon=True).start()

    def _worker(self, item_id: int) -> None:
        try:
            points = api.get_price_history(item_id)
            rl = api.get_rolimons_item(item_id) or {}
        except Exception as e:  # noqa: BLE001
            msg = str(e)
            safe_after(self, lambda: self._fail(item_id, msg))
            return
        safe_after(self, lambda: self._set(item_id, points, rl.get("value"), rl.get("name") or ""))

    def _fail(self, item_id: int, msg: str) -> None:
        if item_id != self.item_id:
            return
        self.points, self.value = [], None
        self.label.configure(text=f"Erro: {msg}")
        self._redraw()

    def _set(self, item_id: int, points: list[dict], value: int | None, name: str) -> None:
        if item_id != self.item_id:
            return
        self.points, self.value, self.name = points, value, name
        if points:
            self.label.configure(text=f"{len(points)} pontos de preço médio (dados do Roblox).")
        else:
            self.label.configure(text="Este item não tem histórico de revenda disponível.")
        self._redraw()

    def restyle(self) -> None:
        self._redraw()

    # ------------------------------------------------------------------
    def _redraw(self) -> None:
        bg, fg, grid = chart_colors()
        self.fig.set_facecolor(bg)
        self.ax.clear()
        self.ax.set_facecolor(bg)
        for sp in self.ax.spines.values():
            sp.set_color(grid)
        self.ax.tick_params(colors=fg)

        if not self.points:
            self.ax.text(0.5, 0.5, "Sem dados de histórico", ha="center", va="center",
                         color=fg, transform=self.ax.transAxes)
            self.ax.set_xticks([])
            self.ax.set_yticks([])
        else:
            xs = [p["date"] for p in self.points]
            ys = [p["price"] for p in self.points]
            self.ax.plot(xs, ys, color="#3b82f6", marker="o", markersize=3, label="Preço médio (RAP)")
            if self.value:
                self.ax.axhline(self.value, color="#22c55e", linestyle="--", label="Value (Rolimons)")
            self.ax.set_ylabel("Robux", color=fg)
            self.ax.set_title(f"Histórico de preço — {self.name or self.item_id}", color=fg)
            self.ax.grid(True, color=grid, alpha=0.5)
            leg = self.ax.legend(facecolor=bg, edgecolor=grid)
            for t in leg.get_texts():
                t.set_color(fg)
            self.fig.autofmt_xdate()
        self.canvas.draw_idle()
