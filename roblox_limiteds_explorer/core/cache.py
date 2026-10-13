"""
Cache em memória com gravação em disco "preguiçosa".

- Leituras/escritas são em memória (rápido).
- O disco só é regravado a cada ~30 s (e ao fechar o app), não a cada `set`.
- Entradas marcadas com persist=False (ex.: dump gigante da Rolimons)
  nunca vão para o disco.
"""
from __future__ import annotations

import atexit
import json
import os
import threading
import time
from typing import Any

from .config import app_dir

CACHE_FILE = app_dir() / "cache.json"
FLUSH_INTERVAL = 30       # segundos entre gravações em disco
MAX_AGE = 24 * 3600       # entradas mais velhas que isso não vão para o disco

_lock = threading.Lock()
_mem: dict[str, dict] = {}
_dirty = False
_last_flush = 0.0


def _load() -> None:
    if not CACHE_FILE.exists():
        return
    try:
        raw = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        now = time.time()
        for k, v in raw.items():
            if isinstance(v, dict) and now - v.get("ts", 0) < MAX_AGE:
                _mem[k] = {"ts": v["ts"], "data": v.get("data"), "persist": True}
    except Exception:
        _mem.clear()


def get(key: str, ttl: int = 300) -> Any | None:
    with _lock:
        entry = _mem.get(key)
    if not entry or time.time() - entry["ts"] > ttl:
        return None
    return entry["data"]


def set(key: str, value: Any, persist: bool = True) -> None:  # noqa: A001
    global _dirty
    with _lock:
        _mem[key] = {"ts": time.time(), "data": value, "persist": persist}
        if persist:
            _dirty = True
    flush()


def flush(force: bool = False) -> None:
    global _dirty, _last_flush
    now = time.time()
    with _lock:
        if not _dirty or (not force and now - _last_flush < FLUSH_INTERVAL):
            return
        snap = {
            k: {"ts": v["ts"], "data": v["data"]}
            for k, v in _mem.items()
            if v.get("persist") and now - v["ts"] < MAX_AGE
        }
        _dirty = False
        _last_flush = now
    try:
        tmp = CACHE_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(snap, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, CACHE_FILE)
    except Exception:
        pass


def clear() -> None:
    global _dirty
    with _lock:
        _mem.clear()
        _dirty = True
    flush(force=True)


_load()
atexit.register(lambda: flush(force=True))
