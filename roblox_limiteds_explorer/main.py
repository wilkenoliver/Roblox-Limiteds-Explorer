"""Ponto de entrada do Roblox Limiteds Explorer."""
from __future__ import annotations

import sys
import traceback

from core.config import app_dir


def _excepthook(exc_type, exc_value, exc_tb) -> None:
    text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    try:
        with open(app_dir() / "error.log", "a", encoding="utf-8") as f:
            f.write(text + "\n")
    except Exception:
        pass
    print(text, file=sys.stderr)


def main() -> int:
    sys.excepthook = _excepthook
    from ui.app import App
    App().mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
