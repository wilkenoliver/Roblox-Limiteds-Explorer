"""
Cliente das APIs públicas do Roblox e da Rolimons.

Todas as funções são síncronas: chame de uma thread (a interface faz isso).
"""
from __future__ import annotations

import threading
import time
from typing import Any

import requests

from . import cache
from .utils import parse_iso

USER_AGENT = "Mozilla/5.0 (compatible; RobloxLimitedsExplorer/2.0)"
TIMEOUT = 15
MAX_RETRIES = 4
BASE_DELAY = 1.0
MIN_INTERVAL = 0.25   # intervalo mínimo entre requisições

_session = requests.Session()
_session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})

_rate_lock = threading.Lock()
_last_call = 0.0
_csrf = {"token": ""}


class ApiError(Exception):
    """Erro com mensagem amigável para mostrar na interface."""


def _throttle() -> None:
    global _last_call
    with _rate_lock:
        wait = MIN_INTERVAL - (time.time() - _last_call)
        if wait > 0:
            time.sleep(wait)
        _last_call = time.time()


def _error_message(resp: requests.Response) -> str:
    try:
        errs = resp.json().get("errors") or []
        if errs and isinstance(errs[0], dict) and errs[0].get("message"):
            return str(errs[0]["message"])
    except Exception:
        pass
    return (resp.text or "")[:150]


def _request(
    method: str,
    url: str,
    *,
    params: dict | None = None,
    json_body: Any = None,
    cookie: str | None = None,
    cache_ttl: int | None = None,
    persist: bool = True,
    forbidden_msg: str | None = None,
) -> Any:
    """HTTP com retry/backoff, tratamento de 429, CSRF (POST) e cache."""
    method = method.upper()
    cache_key = None
    if cache_ttl and method == "GET" and not cookie:
        import json as _json
        cache_key = url + "?" + _json.dumps(params or {}, sort_keys=True, default=str)
        hit = cache.get(cache_key, cache_ttl)
        if hit is not None:
            return hit

    cookies = {".ROBLOSECURITY": cookie} if cookie else None
    delay = BASE_DELAY
    last = "sem resposta"

    for _ in range(MAX_RETRIES):
        _throttle()
        headers = {}
        if method != "GET" and _csrf["token"]:
            headers["x-csrf-token"] = _csrf["token"]
        try:
            resp = _session.request(
                method, url, params=params, json=json_body,
                headers=headers, cookies=cookies, timeout=TIMEOUT,
            )
        except requests.RequestException as e:
            last = str(e)
            time.sleep(delay)
            delay *= 2
            continue

        code = resp.status_code
        if code == 403 and method != "GET" and resp.headers.get("x-csrf-token"):
            _csrf["token"] = resp.headers["x-csrf-token"]
            continue
        if code == 429:
            ra = resp.headers.get("Retry-After", "")
            wait = float(ra) if ra.replace(".", "", 1).isdigit() else delay
            last = "limite de requisições (429)"
            time.sleep(min(wait, 30))
            delay *= 2
            continue
        if code == 401:
            raise ApiError("Não autorizado (401). O cookie .ROBLOSECURITY está inválido ou expirou.")
        if code == 403:
            raise ApiError(forbidden_msg or "Acesso negado (403).")
        if code == 404:
            raise ApiError("Não encontrado (404).")
        if code >= 500:
            last = f"servidor respondeu {code}"
            time.sleep(delay)
            delay *= 2
            continue
        if not resp.ok:
            raise ApiError(f"Erro HTTP {code}: {_error_message(resp)}")

        try:
            data = resp.json()
        except ValueError:
            raise ApiError("Resposta inválida (não é JSON).")
        if cache_key:
            cache.set(cache_key, data, persist=persist)
        return data

    raise ApiError(f"Falha após {MAX_RETRIES} tentativas ({last}).")


def fetch_bytes(url: str, cookie: str | None = None, params: dict | None = None) -> bytes:
    """Baixa um arquivo binário (imagem, asset)."""
    cookies = {".ROBLOSECURITY": cookie} if cookie else None
    for _ in range(3):
        _throttle()
        try:
            resp = _session.get(url, params=params, cookies=cookies, timeout=30)
        except requests.RequestException as e:
            raise ApiError(f"Falha de rede: {e}")
        if resp.status_code == 429:
            time.sleep(3)
            continue
        if resp.status_code in (401, 403):
            raise ApiError(f"Acesso negado ({resp.status_code}). Esse arquivo pode exigir o cookie .ROBLOSECURITY.")
        if resp.status_code == 404:
            raise ApiError("Arquivo não encontrado (404).")
        if not resp.ok:
            raise ApiError(f"Erro HTTP {resp.status_code} ao baixar.")
        return resp.content
    raise ApiError("Limite de requisições ao baixar. Tente de novo em instantes.")


# ---------------------------------------------------------------------------
# Roblox
# ---------------------------------------------------------------------------

def get_item_details(item_id: int) -> dict:
    """Nome, descrição, criador, datas, IsLimited, IsLimitedUnique, preço..."""
    data = _request("GET", f"https://economy.roblox.com/v2/assets/{item_id}/details", cache_ttl=600)
    if not isinstance(data, dict):
        raise ApiError("Formato inesperado em /details.")
    return data


def get_resale_data(item_id: int) -> dict:
    """assetStock (total de cópias), sales, recentAveragePrice, priceDataPoints (histórico)."""
    return _request("GET", f"https://economy.roblox.com/v1/assets/{item_id}/resale-data", cache_ttl=180)


def get_catalog_item(item_id: int) -> dict:
    """Catálogo: lowestResalePrice, itemRestrictions, totalQuantity..."""
    return _request(
        "GET", f"https://catalog.roblox.com/v1/catalog/items/{item_id}/details",
        params={"itemType": "Asset"}, cache_ttl=120,
    )


def search_catalog(keyword: str, limit: int = 10) -> list[dict]:
    data = _request(
        "GET", "https://catalog.roblox.com/v1/search/items/details",
        params={"Category": 1, "Keyword": keyword, "Limit": limit, "SortType": 0},
        cache_ttl=120,
    )
    out = []
    for r in (data.get("data", []) if isinstance(data, dict) else []):
        if r.get("itemType", "Asset") == "Asset" and r.get("id"):
            out.append({"id": int(r["id"]), "name": r.get("name", "?")})
    return out


def get_thumbnail_url(item_id: int, size: str = "420x420") -> str | None:
    data = _request(
        "GET", "https://thumbnails.roblox.com/v1/assets",
        params={"assetIds": str(item_id), "size": size, "format": "Png", "isCircular": "false"},
        cache_ttl=3600,
    )
    for entry in data.get("data", []):
        if entry.get("state") == "Completed" and entry.get("imageUrl"):
            return entry["imageUrl"]
    return None


def get_price_history(item_id: int) -> list[dict]:
    """Histórico REAL de preço médio (priceDataPoints do resale-data)."""
    rs = get_resale_data(item_id)
    pts = []
    for p in rs.get("priceDataPoints") or []:
        dt = parse_iso(p.get("date"))
        if dt is not None and p.get("value") is not None:
            pts.append({"date": dt, "price": p["value"]})
    pts.sort(key=lambda x: x["date"])
    return pts


# ---------------------------------------------------------------------------
# Donos (exige cookie)
# ---------------------------------------------------------------------------

_OWNERS_403 = (
    "Acesso negado (403). O Roblox só deixa listar os donos de um item em alguns casos "
    "(ex.: itens que você criou/possui). Confira o cookie e se a sua conta tem permissão."
)


def get_owners(item_id: int, cookie: str | None, limit: int = 100, cursor: str = "") -> dict:
    if not cookie:
        raise ApiError("Listar donos exige o cookie .ROBLOSECURITY (aba Configurações).")
    params = {"limit": limit, "sortOrder": "Asc"}
    if cursor:
        params["cursor"] = cursor
    return _request(
        "GET", f"https://inventory.roblox.com/v2/assets/{item_id}/owners",
        params=params, cookie=cookie, forbidden_msg=_OWNERS_403,
    )


_names: dict[int, dict] = {}


def get_usernames(user_ids: list[int]) -> dict[int, dict]:
    """Resolve vários IDs de uma vez (endpoint em lote, até 200 por chamada)."""
    ids = [int(i) for i in dict.fromkeys(user_ids) if i]
    todo = [i for i in ids if i not in _names]
    for k in range(0, len(todo), 200):
        chunk = todo[k:k + 200]
        data = _request(
            "POST", "https://users.roblox.com/v1/users",
            json_body={"userIds": chunk, "excludeBannedUsers": False},
        )
        for u in data.get("data", []):
            _names[int(u["id"])] = {"name": u.get("name"), "displayName": u.get("displayName")}
    return {i: _names[i] for i in ids if i in _names}


# ---------------------------------------------------------------------------
# Rolimons
# ---------------------------------------------------------------------------

ROLIMONS_API = "https://www.rolimons.com/itemapi/itemdetails"
ROLIMONS_TTL = 300
_rolimons_lock = threading.Lock()
_rolimons = {"ts": 0.0, "data": None}


def _get_rolimons_all() -> dict:
    with _rolimons_lock:
        now = time.time()
        if _rolimons["data"] and now - _rolimons["ts"] < ROLIMONS_TTL:
            return _rolimons["data"]
        try:
            data = _request("GET", ROLIMONS_API, cache_ttl=ROLIMONS_TTL, persist=False)
            if not isinstance(data, dict) or not data.get("items"):
                raise ApiError("Rolimons devolveu dados vazios.")
        except ApiError:
            if _rolimons["data"]:      # usa a cópia antiga se a nova falhar
                return _rolimons["data"]
            raise
        _rolimons.update(ts=now, data=data)
        return data


def _normalize_rolimons(item_id: int, e: list) -> dict:
    """
    Formato real: [nome, sigla, RAP, VALUE, valor_padrão, demanda, tendência,
                   projetado, hyped, raro].  -1 = sem informação.
    """
    def at(i: int):
        return e[i] if i < len(e) else None

    def pos(v):
        return v if isinstance(v, (int, float)) and v >= 0 else None

    return {
        "id": item_id,
        "name": at(0),
        "acronym": at(1) or None,
        "rap": pos(at(2)),
        "value": pos(at(3)),
        "default_value": pos(at(4)),
        "demand": at(5),
        "trend": at(6),
        "projected": at(7) == 1,
        "hyped": at(8) == 1,
        "rare": at(9) == 1,
    }


def get_rolimons_item(item_id: int) -> dict | None:
    try:
        dump = _get_rolimons_all()
    except ApiError:
        return None
    entry = (dump.get("items") or {}).get(str(item_id))
    return _normalize_rolimons(item_id, entry) if entry else None


def search_rolimons(keyword: str, limit: int = 10) -> list[dict]:
    """Busca por nome/sigla no dump da Rolimons (rápido, sem requisição extra)."""
    kw = keyword.strip().lower()
    if not kw:
        return []
    dump = _get_rolimons_all()
    scored = []
    for sid, e in (dump.get("items") or {}).items():
        name = str(e[0]) if e else ""
        acr = str(e[1]).lower() if len(e) > 1 and e[1] else ""
        lname = name.lower()
        if kw == acr:
            score = 0
        elif lname == kw:
            score = 1
        elif lname.startswith(kw):
            score = 2
        elif kw in lname:
            score = 3
        else:
            continue
        rap = e[2] if len(e) > 2 and isinstance(e[2], (int, float)) else 0
        scored.append((score, -rap, int(sid), name))
    scored.sort()
    return [{"id": i, "name": n} for _, _, i, n in scored[:limit]]


def rolimons_url(item_id: int) -> str:
    return f"https://www.rolimons.com/item/{item_id}"


def roblox_url(item_id: int) -> str:
    return f"https://www.roblox.com/catalog/{item_id}"


# ---------------------------------------------------------------------------
# Utilidades de alto nível
# ---------------------------------------------------------------------------

def resolve_item_id(text: str) -> tuple[int, str]:
    """Aceita ID ou nome. Retorna (id, nome)."""
    text = text.strip()
    if text.isdigit():
        return int(text), ""
    hits = []
    try:
        hits = search_rolimons(text, 1)
    except ApiError:
        pass
    if not hits:
        hits = search_catalog(text, 10)[:1]
    if not hits:
        raise ApiError(f"Nenhum item encontrado para '{text}'.")
    return hits[0]["id"], hits[0]["name"]


def get_full_item(item_id: int) -> dict:
    """Junta tudo sobre um item. Só os detalhes são obrigatórios."""
    full: dict[str, Any] = {"id": item_id, "details": get_item_details(item_id), "errors": []}
    for key, fn in (
        ("resale", get_resale_data),
        ("catalog", get_catalog_item),
        ("rolimons", get_rolimons_item),
    ):
        try:
            full[key] = fn(item_id) or {}
        except ApiError as e:
            full[key] = {}
            full["errors"].append(f"{key}: {e}")
    try:
        full["thumb_url"] = get_thumbnail_url(item_id)
    except ApiError:
        full["thumb_url"] = None
    return full
