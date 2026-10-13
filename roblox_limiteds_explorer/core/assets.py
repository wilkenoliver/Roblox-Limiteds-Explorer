"""Download do arquivo original (textura/modelo) de um item."""
from __future__ import annotations

import re
from pathlib import Path

from . import api

DELIVERY = "https://assetdelivery.roblox.com/v1/asset/?id={}"
_REF = re.compile(rb"asset/?\?id=(\d+)|rbxassetid://(\d+)|assetId=(\d+)", re.I)
MAX_REFS = 8


def _kind(data: bytes) -> tuple[str, str]:
    if data.startswith(b"\x89PNG"):
        return "image", ".png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image", ".jpg"
    if data.startswith(b"version"):
        return "mesh", ".mesh"
    if data.startswith(b"<roblox!"):
        return "container", ".rbxm"
    if data.startswith(b"<roblox"):
        return "container", ".rbxmx"
    return "other", ".bin"


def download_item_assets(item_id: int, folder: str, cookie: str | None = None) -> tuple[list[Path], list[str]]:
    """
    Baixa o asset do item e as texturas/malhas que ele referencia.
    Camisas e calças apontam para outro ID (a imagem da roupa); isso é seguido
    automaticamente. Retorna (arquivos_salvos, avisos).
    """
    out = Path(folder)
    out.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []
    notes: list[str] = []

    data = api.fetch_bytes(DELIVERY.format(item_id), cookie=cookie)
    kind, ext = _kind(data)
    p = out / f"item_{item_id}_original{ext}"
    p.write_bytes(data)
    saved.append(p)
    if kind == "image":
        return saved, notes

    refs: list[int] = []
    for m in _REF.finditer(data):
        rid = int(next(g for g in m.groups() if g))
        if rid != item_id and rid not in refs:
            refs.append(rid)

    if not refs:
        notes.append(
            "Não encontrei texturas referenciadas dentro do arquivo. Em acessórios o modelo vem "
            "em formato binário comprimido, então só o arquivo original foi salvo."
        )
    for rid in refs[:MAX_REFS]:
        try:
            blob = api.fetch_bytes(DELIVERY.format(rid), cookie=cookie)
        except api.ApiError as e:
            notes.append(f"Asset {rid}: {e}")
            continue
        k, e = _kind(blob)
        name = {"image": f"textura_{rid}", "mesh": f"malha_{rid}"}.get(k, f"asset_{rid}")
        p = out / f"{name}{e}"
        p.write_bytes(blob)
        saved.append(p)
    if len(refs) > MAX_REFS:
        notes.append(f"Havia {len(refs)} referências; baixei só as {MAX_REFS} primeiras.")
    return saved, notes
