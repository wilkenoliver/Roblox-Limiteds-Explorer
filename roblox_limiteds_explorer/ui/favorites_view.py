"""Aba "Favoritos": watchlist."""
from __future__ import annotations

import customtkinter as ctk

from core import api
from core.config import config
from core.utils import fmt_robux, trend_label

from .theme import run_bg


class FavoritesView(ctk.CTkFrame):
    def __init__(self, master, app) -> None:
        super().__init__(master, fg_color="transparent")
        self.app = app

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=6, pady=6)
        ctk.CTkLabel(top, text="⭐ Watchlist (favoritos)").pack(side="left")
        ctk.CTkButton(top, text="🔄 Atualizar", width=120, command=self.refresh).pack(side="right", padx=4)

        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.pack(fill="both", expand=True, padx=6, pady=6)
        self.refresh()

    # ------------------------------------------------------------------
    def refresh(self) -> None:
        for w in self.scroll.winfo_children():
            w.destroy()
        favs = config.favorites()
        if not favs:
            ctk.CTkLabel(self.scroll, text="Nenhum favorito ainda. Use ☆ Favoritar na aba Item.").pack(pady=20)
            return
        for fav in favs:
            self._row(fav)

    def _row(self, fav: dict) -> None:
        frame = ctk.CTkFrame(self.scroll)
        frame.pack(fill="x", padx=4, pady=4)

        name = fav.get("name") or "?"
        item_id = fav.get("id")

        ctk.CTkLabel(frame, text=f"{name}  (ID {item_id})", anchor="w", width=300).pack(side="left", padx=6, pady=6)
        info = ctk.CTkLabel(frame, text="carregando...", anchor="w")
        info.pack(side="left", padx=6, fill="x", expand=True)

        ctk.CTkButton(frame, text="Abrir", width=80,
                      command=lambda i=item_id, n=name: self.app.open_item(i, n)).pack(side="right", padx=4)
        ctk.CTkButton(frame, text="🗑", width=40,
                      command=lambda i=item_id: self._remove(i)).pack(side="right", padx=4)

        def work():
            rl = api.get_rolimons_item(item_id) or {}
            try:
                lowest = api.get_catalog_item(item_id).get("lowestResalePrice")
            except api.ApiError:
                lowest = None
            return (f"Value: {fmt_robux(rl.get('value'))}  |  RAP: {fmt_robux(rl.get('rap'))}  |  "
                    f"Menor: {fmt_robux(lowest)}  |  {trend_label(rl.get('trend'))}")

        def done(res, err):
            try:
                info.configure(text=res if res else f"erro: {err}")
            except Exception:  # linha já foi removida
                pass

        run_bg(self, work, done)

    def _remove(self, item_id: int) -> None:
        config.remove_favorite(item_id)
        self.refresh()
