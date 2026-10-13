"""Formatação, exportação, notificações e cálculo de lucro."""
from __future__ import annotations

import csv
import json
import re
from datetime import datetime
from typing import Any


# ---------------------------------------------------------------------------
# Formatação
# ---------------------------------------------------------------------------

def fmt_number(n: Any) -> str:
    try:
        return f"{int(n):,}".replace(",", ".")
    except (TypeError, ValueError):
        return str(n)


def fmt_robux(n: Any) -> str:
    if n is None or n == "":
        return "—"
    return f"{fmt_number(n)} Robux"


def parse_iso(value: Any) -> datetime | None:
    """Converte datas ISO do Roblox (frações de qualquer tamanho, 'Z')."""
    if isinstance(value, datetime):
        return value
    if not value or not isinstance(value, str):
        return None
    s = value.strip().replace("Z", "+00:00")
    s = re.sub(r"\.(\d+)", lambda m: "." + m.group(1)[:6].ljust(6, "0"), s, count=1)
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def fmt_date(value: Any) -> str:
    dt = parse_iso(value)
    if dt is None:
        return str(value) if value else "—"
    if dt.tzinfo is not None:
        dt = dt.astimezone()
    return dt.strftime("%d/%m/%Y %H:%M")


# Rolimons: -1 = sem informação
_DEMAND = {0: "Terrível", 1: "Baixa", 2: "Normal", 3: "Alta", 4: "Incrível"}
_TREND = {0: "⚠ Instável", 1: "📉 Caindo", 2: "➖ Estável", 3: "📈 Subindo", 4: "〰 Flutuando"}


def demand_label(v: Any) -> str:
    return _DEMAND.get(v, "—")


def trend_label(v: Any) -> str:
    return _TREND.get(v, "—")


# ---------------------------------------------------------------------------
# Exportação
# ---------------------------------------------------------------------------

def export_csv(path: str, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    if not rows:
        raise ValueError("Nada para exportar.")
    fieldnames = fieldnames or list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def export_json(path: str, data: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)


# ---------------------------------------------------------------------------
# Notificações
# ---------------------------------------------------------------------------

def notify(title: str, message: str) -> None:
    try:
        from plyer import notification
        notification.notify(title=title, message=message, timeout=8, app_name="Roblox Limiteds")
    except Exception:
        print(f"[NOTIFY] {title}: {message}")


# ---------------------------------------------------------------------------
# Calculadora (Roblox fica com 30% da venda)
# ---------------------------------------------------------------------------

def profit_calc(buy_price: Any, sell_price: Any) -> dict:
    buy = max(0, int(buy_price or 0))
    sell = max(0, int(sell_price or 0))
    net = sell * 7 // 10                       # 70% para o vendedor (inteiro)
    profit = net - buy
    roi = (profit / buy * 100) if buy else 0.0
    breakeven = -(-buy * 10 // 7) if buy else 0  # menor venda sem prejuízo
    return {
        "buy_price": buy,
        "sell_price": sell,
        "fee": sell - net,
        "net_received": net,
        "profit": profit,
        "roi_percent": round(roi, 2),
        "breakeven_price": breakeven,
    }
