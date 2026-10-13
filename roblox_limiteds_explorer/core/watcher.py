"""Verificação em segundo plano da watchlist (RAP e menor preço)."""
from __future__ import annotations

import json
import os
import threading
from typing import Callable

from . import api
from .config import app_dir, config
from .utils import notify

STATE_FILE = app_dir() / "watcher_state.json"


class Watcher:
    def __init__(self, on_event: Callable[[str], None] | None = None) -> None:
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self.on_event = on_event
        self._state: dict[str, dict] = {}
        self._load_state()

    # ------------------------------------------------------------------
    def _load_state(self) -> None:
        try:
            if STATE_FILE.exists():
                self._state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            self._state = {}

    def _save_state(self) -> None:
        try:
            tmp = STATE_FILE.with_suffix(".tmp")
            tmp.write_text(json.dumps(self._state, indent=2), encoding="utf-8")
            os.replace(tmp, STATE_FILE)
        except Exception:
            pass

    # ------------------------------------------------------------------
    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        t = self._thread
        if t and t.is_alive() and t is not threading.current_thread():
            t.join(timeout=3)

    def _emit(self, msg: str) -> None:
        if self.on_event:
            try:
                self.on_event(msg)
            except Exception:
                pass

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                if config.get("watch_enabled") and config.favorites():
                    self._check_all()
            except Exception as e:
                self._emit(f"[watcher] erro: {e}")
            minutes = max(1, int(config.get("watch_interval_min", 15) or 15))
            if self._stop.wait(minutes * 60):
                return

    # ------------------------------------------------------------------
    def _check_all(self) -> None:
        for fav in config.favorites():
            if self._stop.is_set():
                return
            item_id = fav.get("id")
            if not item_id:
                continue
            try:
                rl = api.get_rolimons_item(item_id) or {}
                try:
                    lowest = api.get_catalog_item(item_id).get("lowestResalePrice")
                except api.ApiError:
                    lowest = None
            except api.ApiError:
                continue

            rap, value = rl.get("rap"), rl.get("value")
            key = str(item_id)
            prev = self._state.get(key, {})
            changed: list[str] = []
            if rap is not None and prev.get("rap") not in (None, rap):
                changed.append(f"RAP: {prev['rap']} → {rap}")
            if lowest is not None and prev.get("lowest") not in (None, lowest):
                changed.append(f"Menor preço: {prev['lowest']} → {lowest}")

            self._state[key] = {"rap": rap, "lowest": lowest, "value": value}
            self._save_state()

            if changed and config.get("notify_on_change"):
                name = fav.get("name") or rl.get("name") or f"Item {item_id}"
                msg = f"{name}\n" + "\n".join(changed)
                notify("Mudança em item favorito", msg)
                self._emit(msg.replace("\n", " | "))


watcher = Watcher()
