"""Janela principal."""
from __future__ import annotations

import threading
import traceback

import customtkinter as ctk

from core import api
from core.config import app_dir, config
from core.watcher import watcher

from .calculator_view import CalculatorView
from .chart_view import ChartView
from .compare_view import CompareView
from .favorites_view import FavoritesView
from .item_view import ItemView
from .owners_view import OwnersView
from .settings_view import SettingsView
from .theme import apply_treeview_style, run_bg, safe_after

ctk.set_default_color_theme("blue")

_SEP = " — "
_IGNORE_KEYS = {"Return", "Escape", "Tab", "Up", "Down", "Left", "Right",
                "Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R"}


class App(ctk.CTk):
    def __init__(self) -> None:
        mode = "dark" if config.get("theme", "dark") == "dark" else "light"
        ctk.set_appearance_mode(mode)
        super().__init__()
        self.title("Roblox Limiteds Explorer")
        self.geometry("1180x780")
        self.minsize(1000, 680)

        self.current_item_id: int | None = None
        self.current_summary: dict | None = None
        self._ac_job = None

        apply_treeview_style()
        self._build_ui()

        watcher.on_event = lambda msg: safe_after(self, lambda: self.set_status(f"🔔 {msg}"))
        if config.get("watch_enabled"):
            watcher.start()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        top = ctk.CTkFrame(self, corner_radius=0)
        top.pack(fill="x")

        ctk.CTkLabel(top, text="🔎 Roblox Limiteds", font=ctk.CTkFont(size=18, weight="bold")).pack(
            side="left", padx=12, pady=10)

        self.entry = ctk.CTkEntry(top, width=340, placeholder_text="ID ou nome do item")
        self.entry.pack(side="left", padx=6, pady=10)
        self.entry.bind("<Return>", lambda e: self.on_search())
        self.entry.bind("<KeyRelease>", self._on_key)

        ctk.CTkButton(top, text="Buscar", width=90, command=self.on_search).pack(side="left", padx=6, pady=10)

        self.suggest_box = ctk.CTkComboBox(top, values=[""], width=300, command=self._pick_suggestion)
        self.suggest_box.pack(side="left", padx=6, pady=10)
        self.suggest_box.set("Sugestões")

        ctk.CTkButton(top, text="🌗 Tema", width=90, command=self.toggle_theme).pack(side="right", padx=10, pady=10)

        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=10)
        names = ["Item", "Donos", "Histórico", "Comparar", "Favoritos", "Calculadora", "Configurações"]
        frames = {n: self.tabs.add(n) for n in names}

        self.view_item = ItemView(frames["Item"], self)
        self.view_owners = OwnersView(frames["Donos"], self)
        self.view_chart = ChartView(frames["Histórico"], self)
        self.view_compare = CompareView(frames["Comparar"], self)
        self.view_fav = FavoritesView(frames["Favoritos"], self)
        self.view_calc = CalculatorView(frames["Calculadora"], self)
        self.view_settings = SettingsView(frames["Configurações"], self)
        for v in (self.view_item, self.view_owners, self.view_chart, self.view_compare,
                  self.view_fav, self.view_calc, self.view_settings):
            v.pack(fill="both", expand=True)

        self.status = ctk.CTkLabel(self, text="Pronto.", anchor="w")
        self.status.pack(fill="x", padx=12, pady=(0, 6))

    # ------------------------------------------------------------------
    # Tema
    # ------------------------------------------------------------------
    def set_theme(self, value: str) -> None:
        value = "dark" if value == "dark" else "light"
        config.set("theme", value)
        ctk.set_appearance_mode(value)
        apply_treeview_style()
        self.view_chart.restyle()
        try:
            self.view_settings.theme_var.set(value)
        except Exception:
            pass

    def toggle_theme(self) -> None:
        self.set_theme("light" if config.get("theme", "dark") == "dark" else "dark")

    def set_status(self, text: str) -> None:
        self.status.configure(text=text)

    # ------------------------------------------------------------------
    # Busca
    # ------------------------------------------------------------------
    def on_search(self) -> None:
        raw = self.entry.get().strip()
        if not raw:
            return
        self.set_status(f"Buscando '{raw}'...")
        threading.Thread(target=self._search_worker, args=(raw,), daemon=True).start()

    def _search_worker(self, raw: str) -> None:
        try:
            if raw.isdigit():
                item_id = int(raw)
                name = api.get_item_details(item_id).get("Name", raw)
                safe_after(self, lambda: self.open_item(item_id, name))
                return

            results = []
            try:
                results = api.search_rolimons(raw, 12)
            except api.ApiError:
                pass
            if not results:
                results = api.search_catalog(raw, 10)
            if not results:
                safe_after(self, lambda: self.set_status(f"Nenhum item encontrado para '{raw}'."))
                return
            opts = [f"{r['id']}{_SEP}{r['name']}" for r in results]
            first = results[0]
            safe_after(self, lambda: self._populate_suggestions(opts))
            safe_after(self, lambda: self.open_item(first["id"], first["name"]))
        except Exception as e:  # noqa: BLE001
            msg = str(e)
            safe_after(self, lambda: self.set_status(f"Erro: {msg}"))

    def _on_key(self, event) -> None:
        if event.keysym in _IGNORE_KEYS:
            return
        if self._ac_job:
            self.after_cancel(self._ac_job)
        self._ac_job = self.after(350, self._autocomplete)

    def _autocomplete(self) -> None:
        self._ac_job = None
        text = self.entry.get().strip()
        if len(text) < 2 or text.isdigit():
            return

        def work():
            return api.search_rolimons(text, 12)

        def done(res, err):
            if err or not res or self.entry.get().strip() != text:
                return
            self._populate_suggestions([f"{r['id']}{_SEP}{r['name']}" for r in res], select=False)

        run_bg(self, work, done)

    def _populate_suggestions(self, opts: list[str], select: bool = True) -> None:
        self.suggest_box.configure(values=opts)
        if select and opts:
            self.suggest_box.set(opts[0])

    def _pick_suggestion(self, value: str) -> None:
        if _SEP in value:
            sid, name = value.split(_SEP, 1)
            if sid.strip().isdigit():
                self.open_item(int(sid), name.strip())

    def open_item(self, item_id: int, name: str) -> None:
        self.current_item_id = item_id
        self.current_summary = None
        self.set_status(f"Item {item_id} — {name}")
        self.view_item.load_item(item_id)
        self.view_owners.set_item(item_id)
        self.view_chart.load_item(item_id)
        self.tabs.set("Item")

    # ------------------------------------------------------------------
    def report_callback_exception(self, exc, val, tb) -> None:
        """Erros dentro de callbacks do Tk: registra em arquivo (útil no .exe sem console)."""
        text = "".join(traceback.format_exception(exc, val, tb))
        try:
            with open(app_dir() / "error.log", "a", encoding="utf-8") as f:
                f.write(text + "\n")
        except Exception:
            pass
        print(text)
        self.set_status(f"Erro inesperado: {val}")

    def _on_close(self) -> None:
        try:
            watcher.stop()
        except Exception:
            pass
        self.destroy()
