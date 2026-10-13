"""Transforma os dados crus de um item em campos/texto para a interface."""
from __future__ import annotations

from .utils import demand_label, fmt_date, fmt_number, fmt_robux, parse_iso, trend_label

ASSET_TYPES = {
    2: "Camiseta (T-Shirt)", 8: "Chapéu", 11: "Camisa", 12: "Calça", 17: "Cabeça", 18: "Rosto",
    19: "Gear", 41: "Acessório de cabelo", 42: "Acessório de rosto", 43: "Acessório de pescoço",
    44: "Acessório de ombro", 45: "Acessório frontal", 46: "Acessório de costas",
    47: "Acessório de cintura", 64: "Camiseta (acessório)", 65: "Camisa (acessório)",
    66: "Calça (acessório)", 67: "Jaqueta", 68: "Suéter", 69: "Shorts",
    70: "Sapato esquerdo", 71: "Sapato direito", 72: "Vestido/saia",
}


def summarize(full: dict) -> dict:
    d = full.get("details") or {}
    rs = full.get("resale") or {}
    ct = full.get("catalog") or {}
    rl = full.get("rolimons") or {}
    creator = d.get("Creator") or {}

    restrictions = ct.get("itemRestrictions") or []
    is_unique = bool(d.get("IsLimitedUnique")) or "LimitedUnique" in restrictions
    is_limited = bool(d.get("IsLimited")) or is_unique or "Limited" in restrictions or "Collectible" in restrictions

    dates = [dt for dt in (parse_iso(p.get("date")) for p in rs.get("priceDataPoints") or []) if dt]

    lowest = ct.get("lowestResalePrice")
    if lowest is None and is_limited:
        lowest = ct.get("lowestPrice")

    return {
        "id": full.get("id"),
        "name": d.get("Name") or rl.get("name") or "?",
        "description": d.get("Description") or "",
        "type": ASSET_TYPES.get(d.get("AssetTypeId"), f"Tipo {d.get('AssetTypeId')}" if d.get("AssetTypeId") else "—"),
        "creator_name": creator.get("Name") or "?",
        "creator_id": creator.get("CreatorTargetId") or creator.get("Id"),
        "created": d.get("Created"),
        "updated": d.get("Updated"),
        "is_limited": is_limited,
        "is_unique": is_unique,
        "original_price": d.get("PriceInRobux") if d.get("PriceInRobux") is not None else rs.get("originalPrice"),
        "for_sale": d.get("IsForSale"),
        "stock_left": d.get("Remaining") if d.get("Remaining") is not None else rs.get("numberRemaining"),
        "total_copies": rs.get("assetStock"),
        "sales": rs.get("sales"),
        "lowest": lowest,
        "rap_roblox": rs.get("recentAveragePrice"),
        "first_record": min(dates) if dates else None,
        "last_record": max(dates) if dates else None,
        "rap": rl.get("rap"),
        "value": rl.get("value"),
        "default_value": rl.get("default_value"),
        "demand": rl.get("demand"),
        "trend": rl.get("trend"),
        "projected": rl.get("projected"),
        "hyped": rl.get("hyped"),
        "rare": rl.get("rare"),
        "in_rolimons": bool(rl),
    }


def _yn(v) -> str:
    return "Sim" if v else "Não"


def report_text(full: dict) -> str:
    s = summarize(full)
    L = [
        f"🆔 ID: {s['id']}",
        f"🧩 Tipo: {s['type']}",
        f"👤 Criador: {s['creator_name']} (ID {s['creator_id']})",
        f"📅 Criado em: {fmt_date(s['created'])}",
        f"♻ Atualizado em: {fmt_date(s['updated'])}",
        f"🔒 Limited: {_yn(s['is_limited'])}" + ("  (Limited U — numerado)" if s["is_unique"] else ""),
        f"🏷 Preço original: {fmt_robux(s['original_price'])}",
        f"🛒 À venda na loja: {_yn(s['for_sale'])}",
        "",
        "─── Cópias e vendas ───",
        f"📦 Total de cópias (Limited U): {fmt_number(s['total_copies']) if s['total_copies'] is not None else '—'}",
        f"📉 Estoque restante na loja: {fmt_number(s['stock_left']) if s['stock_left'] is not None else '—'}",
        f"🧾 Vendas registradas: {fmt_number(s['sales']) if s['sales'] is not None else '—'}",
        f"🕒 1º registro de revenda: {fmt_date(s['first_record'])}",
        "   (aprox. de quando virou limited negociável; o Roblox não informa a data exata)",
        "",
        "─── Mercado (Roblox) ───",
        f"💰 Menor preço de revenda: {fmt_robux(s['lowest'])}",
        f"📈 RAP (Roblox): {fmt_robux(s['rap_roblox'])}",
        "",
        "─── Rolimons ───",
    ]
    if s["in_rolimons"]:
        flags = [n for n, on in (("Projetado", s["projected"]), ("Hyped", s["hyped"]), ("Raro", s["rare"])) if on]
        L += [
            f"💎 Value: {fmt_robux(s['value'])}",
            f"📈 RAP: {fmt_robux(s['rap'])}",
            f"📊 Tendência: {trend_label(s['trend'])}",
            f"🔥 Demanda: {demand_label(s['demand'])}",
            f"🚩 Marcações: {', '.join(flags) if flags else 'nenhuma'}",
        ]
    else:
        L.append("Item não encontrado na Rolimons (não é limited ou ainda não listado).")
    L += ["", "─── Descrição ───", s["description"] or "(sem descrição)"]
    if full.get("errors"):
        L += ["", "─── Avisos ───"] + [f"• {e}" for e in full["errors"]]
    return "\n".join(L)
