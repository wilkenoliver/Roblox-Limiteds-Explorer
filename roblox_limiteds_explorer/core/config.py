"""
Configurações do aplicativo.

Arquivo: %APPDATA%\\RobloxLimitedsExplorer\\config.json
O cookie .ROBLOSECURITY vai para o Gerenciador de Credenciais do Windows
(via `keyring`) quando disponível; só cai no config.json se o keyring falhar.
"""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any

APP_NAME = "RobloxLimitedsExplorer"
KEYRING_USER = "roblosecurity"


def app_dir() -> Path:
    base = os.environ.get("APPDATA") or str(Path.home())
    p = Path(base) / APP_NAME
    p.mkdir(parents=True, exist_ok=True)
    return p


def export_dir() -> Path:
    base = os.environ.get("USERPROFILE") or str(Path.home())
    p = Path(base) / "Documents" / APP_NAME
    p.mkdir(parents=True, exist_ok=True)
    return p


CONFIG_FILE = app_dir() / "config.json"

DEFAULTS: dict[str, Any] = {
    "theme": "dark",            # "dark" | "light"
    "roblosecurity": "",        # só usado se o keyring não estiver disponível
    "watch_interval_min": 15,
    "watch_enabled": False,
    "notify_on_change": True,
    "favorites": [],            # [{id, name}]
}


class Config:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._data: dict[str, Any] = {k: (list(v) if isinstance(v, list) else v) for k, v in DEFAULTS.items()}
        self.load()

    # ------------------------------------------------------------------
    def load(self) -> None:
        with self._lock:
            if CONFIG_FILE.exists():
                try:
                    loaded = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                    if isinstance(loaded, dict):
                        self._data.update(loaded)
                except Exception:
                    pass

    def save(self) -> None:
        with self._lock:
            try:
                tmp = CONFIG_FILE.with_suffix(".tmp")
                tmp.write_text(json.dumps(self._data, indent=2, ensure_ascii=False), encoding="utf-8")
                os.replace(tmp, CONFIG_FILE)
            except Exception:
                pass

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._data[key] = value
            self.save()

    # ------------------------------------------------------------------
    # Cookie
    # ------------------------------------------------------------------
    def get_cookie(self) -> str:
        try:
            import keyring
            value = keyring.get_password(APP_NAME, KEYRING_USER)
            if value:
                return value
        except Exception:
            pass
        return self.get("roblosecurity", "") or ""

    def set_cookie(self, value: str) -> bool:
        """Salva (ou apaga) o cookie. Retorna True se foi para o cofre do sistema."""
        value = (value or "").strip()
        secure = False
        try:
            import keyring
            if value:
                keyring.set_password(APP_NAME, KEYRING_USER, value)
            else:
                try:
                    keyring.delete_password(APP_NAME, KEYRING_USER)
                except Exception:
                    pass
            secure = True
        except Exception:
            secure = False
        with self._lock:
            self._data["roblosecurity"] = "" if secure else value
            self.save()
        return secure

    # ------------------------------------------------------------------
    # Favoritos
    # ------------------------------------------------------------------
    def favorites(self) -> list[dict]:
        with self._lock:
            return [dict(f) for f in self._data.get("favorites", [])]

    def is_favorite(self, item_id: int) -> bool:
        with self._lock:
            return any(f.get("id") == item_id for f in self._data.get("favorites", []))

    def add_favorite(self, item_id: int, name: str) -> None:
        with self._lock:
            favs = self._data.setdefault("favorites", [])
            if not any(f.get("id") == item_id for f in favs):
                favs.append({"id": item_id, "name": name})
                self.save()

    def remove_favorite(self, item_id: int) -> None:
        with self._lock:
            self._data["favorites"] = [f for f in self._data.get("favorites", []) if f.get("id") != item_id]
            self.save()


config = Config()
