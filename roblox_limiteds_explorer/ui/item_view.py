"""Aba "Item": detalhes, imagem, Rolimons, cópias, downloads."""
from __future__ import annotations

import io
import threading
import webbrowser
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image

from core import api, assets
from core.config import config, export_dir
from core.report import report_text, summarize
from core.utils import export_json

from .theme import run_bg, safe_after

THUMB = 260


class ItemView(ctk.CTkFrame):
    def __init__(self, master, app) -> None:
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.item_id: int | None = None
        self.full: dict | None = None
        self._thumb_ref = None
        self._blank = ctk.CTkImage(Image.new("RGBA", (1, 1), (0, 0, 0, 0)), size=(THUMB, THUMB))
        self._build()

    # ------------------------------------------------------------------
    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(self)
        left.grid(row=0, column=0, sticky="ns", padx=(0, 10))

        self.thumb_label = ctk.CTkLabel(left, text="(sem imagem)", image=self._blank,
                                        width=THUMB, height=THUMB)
        self.thumb_label.pack(padx=12, pady=12)

        for text, cmd in [
            ("⬇ Baixar imagem", self.download_image),
            ("⬇ Baixar textura/modelo", self.download_asset),
            ("🌐 Abrir no Roblox", self.open_roblox),
            ("📊 Abrir no Rolimons", self.open_rolimons),
            ("📤 Exportar JSON", self.export_json_current),
        ]:
            ctk.CTkButton(left, text=text, command=cmd).pack(fill="x", padx=12, pady=4)

        self.fav_btn = ctk.CTkButton(left, text="☆ Favoritar", command=self.toggle_favorite)
        self.fav_btn.pack(fill="x", padx=12, pady=(12, 12))

        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        self.title_lbl = ctk.CTkLabel(
            right, text="Nenhum item carregado. Busque por ID ou nome acima.",
            font=ctk.CTkFont(size=20, weight="bold"), anchor="w", justify="left",
        )
        self.title_lbl.grid(row=0, column=0, sticky="ew", padx=6, pady=(4, 8))

        self.info = ctk.CTkTextbox(right, wrap="word")
        self.info.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0, 6))
        self.info.configure(state="disabled")

    # ------------------------------------------------------------------
    def load_item(self, item_id: int) -> None:
        self.item_id = item_id
        self.full = None
        self.title_lbl.configure(text=f"Carregando item {item_id}...")
        self._set_info("Buscando dados...")
        self.thumb_label.configure(image=self._blank, text="(carregando...)")
        threading.Thread(target=self._worker, args=(item_id,), daemon=True).start()

    def _worker(self, item_id: int) -> None:
        try:
            full = api.get_full_item(item_id)
        except Exception as e:  # noqa: BLE001
            msg = str(e)
            safe_after(self, lambda: self._on_error(item_id, msg))
            return
        safe_after(self, lambda: self._render(item_id, full))

        url = full.get("thumb_url")
        if not url:
            safe_after(self, lambda: self._no_thumb(item_id))
            return
        try:
            img = Image.open(io.BytesIO(api.fetch_bytes(url))).convert("RGBA")
            img = img.resize((THUMB, THUMB), Image.Resampling.LANCZOS)
        except Exception:  # noqa: BLE001
            safe_after(self, lambda: self._no_thumb(item_id))
            return
        safe_after(self, lambda: self._show_thumb(item_id, img))

    # ------------------------------------------------------------------
    def _on_error(self, item_id: int, msg: str) -> None:
        if item_id != self.item_id:
            return
        self.title_lbl.configure(text="Erro ao carregar o item.")
        self._set_info(f"❌ {msg}")
        self.thumb_label.configure(image=self._blank, text="(sem imagem)")
        self.app.set_status(f"Erro: {msg}")

    def _render(self, item_id: int, full: dict) -> None:
        if item_id != self.item_id:
            return
        self.full = full
        s = summarize(full)
        self.app.current_summary = s
        self.title_lbl.configure(text=f"{s['name']}  (ID {item_id})")
        self.fav_btn.configure(text="★ Remover favorito" if config.is_favorite(item_id) else "☆ Favoritar")
        self._set_info(report_text(full))
        self.app.set_status(f"Item {item_id} — {s['name']}")

    def _show_thumb(self, item_id: int, img: Image.Image) -> None:
        if item_id != self.item_id:
            return
        self._thumb_ref = ctk.CTkImage(light_image=img, dark_image=img, size=(THUMB, THUMB))
        self.thumb_label.configure(image=self._thumb_ref, text="")

    def _no_thumb(self, item_id: int) -> None:
        if item_id == self.item_id:
            self.thumb_label.configure(image=self._blank, text="(sem imagem)")

    def _set_info(self, text: str) -> None:
        self.info.configure(state="normal")
        self.info.delete("1.0", "end")
        self.info.insert("1.0", text)
        self.info.configure(state="disabled")

    # ------------------------------------------------------------------
    # Downloads
    # ------------------------------------------------------------------
    def download_image(self) -> None:
        if not self.item_id:
            return
        item_id = self.item_id
        path = filedialog.asksaveasfilename(
            defaultextension=".png", initialdir=str(export_dir()),
            initialfile=f"item_{item_id}.png", filetypes=[("PNG", "*.png")],
        )
        if not path:
            return
        self.app.set_status("Baixando imagem...")

        def work():
            url = api.get_thumbnail_url(item_id, "700x700")
            if not url:
                raise api.ApiError("Imagem ainda não disponível no Roblox.")
            with open(path, "wb") as f:
                f.write(api.fetch_bytes(url))
            return path

        def done(res, err):
            self.app.set_status("Pronto.")
            if err:
                messagebox.showerror("Download", f"Falha: {err}")
            else:
                messagebox.showinfo("Download", f"Imagem salva em:\n{res}")

        run_bg(self, work, done)

    def download_asset(self) -> None:
        if not self.item_id:
            return
        item_id = self.item_id
        folder = filedialog.askdirectory(title="Pasta para salvar textura/modelo",
                                         initialdir=str(export_dir()))
        if not folder:
            return
        cookie = config.get_cookie() or None
        self.app.set_status("Baixando textura/modelo...")

        def work():
            return assets.download_item_assets(item_id, folder, cookie)

        def done(res, err):
            self.app.set_status("Pronto.")
            if err:
                messagebox.showerror(
                    "Download",
                    f"Falha: {err}\n\nAlguns assets exigem o cookie .ROBLOSECURITY (aba Configurações).",
                )
                return
            saved, notes = res
            text = "Arquivos salvos:\n" + "\n".join(f"• {p.name}" for p in saved)
            if notes:
                text += "\n\nAvisos:\n" + "\n".join(f"• {n}" for n in notes)
            messagebox.showinfo("Download", f"{text}\n\nPasta: {folder}")

        run_bg(self, work, done)

    # ------------------------------------------------------------------
    def open_roblox(self) -> None:
        if self.item_id:
            webbrowser.open(api.roblox_url(self.item_id))

    def open_rolimons(self) -> None:
        if self.item_id:
            webbrowser.open(api.rolimons_url(self.item_id))

    def toggle_favorite(self) -> None:
        if not self.item_id:
            return
        name = (self.app.current_summary or {}).get("name") or f"Item {self.item_id}"
        if config.is_favorite(self.item_id):
            config.remove_favorite(self.item_id)
            self.fav_btn.configure(text="☆ Favoritar")
            self.app.set_status(f"Removido dos favoritos: {name}")
        else:
            config.add_favorite(self.item_id, name)
            self.fav_btn.configure(text="★ Remover favorito")
            self.app.set_status(f"Adicionado aos favoritos: {name}")
        self.app.view_fav.refresh()

    def export_json_current(self) -> None:
        if not self.item_id or not self.full:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".json", initialdir=str(export_dir()),
            initialfile=f"item_{self.item_id}.json", filetypes=[("JSON", "*.json")],
        )
        if not path:
            return
        try:
            export_json(path, self.full)
            messagebox.showinfo("Exportar", f"JSON salvo em:\n{path}")
        except Exception as e:  # noqa: BLE001
            messagebox.showerror("Exportar", f"Falha: {e}")
