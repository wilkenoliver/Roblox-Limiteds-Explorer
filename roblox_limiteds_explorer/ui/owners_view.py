"""Aba "Donos": lista paginada de quem tem o item (exige cookie) + CSV."""
from __future__ import annotations

import threading
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk

from core import api
from core.config import config, export_dir
from core.utils import export_csv, fmt_date

from .theme import safe_after

FIELDS = ["username", "user_id", "uaid", "serial", "obtained"]
MAX_PAGES_ALL = 50   # "Carregar tudo": até 50 páginas x 100 = 5.000 donos


class OwnersView(ctk.CTkFrame):
    def __init__(self, master, app) -> None:
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.item_id: int | None = None
        self.cursors: list[str] = [""]          # cursor de cada página
        self.pages: dict[int, list[dict]] = {}  # linhas já carregadas por página
        self.page = 0
        self.next_cursor = ""
        self._busy = False
        self._build()

    # ------------------------------------------------------------------
    def _build(self) -> None:
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=6, pady=6)

        self.info_lbl = ctk.CTkLabel(
            top, anchor="w", justify="left", wraplength=420,
            text="Busque um item. Listar donos exige o cookie .ROBLOSECURITY (Configurações).",
        )
        self.info_lbl.pack(side="left", fill="x", expand=True)

        for text, w, cmd in [
            ("📤 CSV", 80, self.export_csv),
            ("⏬ Carregar tudo", 130, self.load_all),
            ("Próxima ▶", 100, self.next_page),
            ("◀ Anterior", 100, self.prev_page),
            ("🔄 Carregar", 100, self.reload),
        ]:
            ctk.CTkButton(top, text=text, width=w, command=cmd).pack(side="right", padx=3)

        frame = ctk.CTkFrame(self)
        frame.pack(fill="both", expand=True, padx=6, pady=6)

        self.tree = ttk.Treeview(frame, columns=FIELDS, show="headings")
        for c, t, w in [
            ("username", "Usuário", 200), ("user_id", "ID do usuário", 120),
            ("uaid", "UAID", 130), ("serial", "Série #", 80), ("obtained", "Obtido em", 160),
        ]:
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor="w")
        sb = ctk.CTkScrollbar(frame, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True, side="left")

        self.page_lbl = ctk.CTkLabel(self, text="")
        self.page_lbl.pack(pady=(0, 6))

    # ------------------------------------------------------------------
    def set_item(self, item_id: int) -> None:
        self.item_id = item_id
        self.cursors, self.pages, self.page, self.next_cursor = [""], {}, 0, ""
        self._clear()
        self.page_lbl.configure(text="")
        self.info_lbl.configure(text=f"Item {item_id}. Clique em “Carregar” para buscar os donos.")

    def reload(self) -> None:
        if not self.item_id:
            return
        self.cursors, self.pages, self.page, self.next_cursor = [""], {}, 0, ""
        self._fetch()

    def next_page(self) -> None:
        if self.next_cursor and not self._busy:
            self.cursors = self.cursors[: self.page + 1] + [self.next_cursor]
            self.page += 1
            self._fetch()

    def prev_page(self) -> None:
        if self.page > 0 and not self._busy:
            self.page -= 1
            if self.page in self.pages:
                self._render(self.pages[self.page], f"Página {self.page + 1}")
            else:
                self._fetch()

    # ------------------------------------------------------------------
    def _check_ready(self) -> str | None:
        if not self.item_id:
            return None
        cookie = config.get_cookie()
        if not cookie:
            self.info_lbl.configure(text="⚠ Configure o cookie .ROBLOSECURITY na aba Configurações.")
            return None
        return cookie

    def _fetch(self) -> None:
        cookie = self._check_ready()
        if not cookie or self._busy:
            return
        self._busy = True
        self.info_lbl.configure(text="Buscando donos...")
        args = (self.item_id, cookie, self.cursors[self.page], self.page)
        threading.Thread(target=self._worker, args=args, daemon=True).start()

    def _load_page(self, item_id: int, cookie: str, cursor: str) -> tuple[list[dict], str]:
        data = api.get_owners(item_id, cookie, limit=100, cursor=cursor)
        entries = data.get("data", []) if isinstance(data, dict) else []
        uids = [(e.get("owner") or {}).get("id") for e in entries]
        try:
            names = api.get_usernames([u for u in uids if u])
        except api.ApiError:
            names = {}
        rows = []
        for e, uid in zip(entries, uids):
            rows.append({
                "username": (names.get(uid) or {}).get("name") or (f"user_{uid}" if uid else "—"),
                "user_id": uid or "—",
                "uaid": e.get("id", "—"),
                "serial": e.get("serialNumber") if e.get("serialNumber") is not None else "—",
                "obtained": fmt_date(e.get("created")),
            })
        return rows, (data.get("nextPageCursor") or "") if isinstance(data, dict) else ""

    def _worker(self, item_id: int, cookie: str, cursor: str, page: int) -> None:
        try:
            rows, nxt = self._load_page(item_id, cookie, cursor)
        except Exception as e:  # noqa: BLE001
            msg = str(e)
            safe_after(self, lambda: self._fail(msg))
            return
        safe_after(self, lambda: self._done_page(item_id, page, rows, nxt))

    def _done_page(self, item_id: int, page: int, rows: list[dict], nxt: str) -> None:
        self._busy = False
        if item_id != self.item_id:
            return
        self.pages[page] = rows
        self.next_cursor = nxt
        self._render(rows, f"Página {page + 1}" + ("" if nxt else " (última)"))

    def _fail(self, msg: str) -> None:
        self._busy = False
        self.info_lbl.configure(text=f"❌ {msg}")

    # ------------------------------------------------------------------
    def load_all(self) -> None:
        cookie = self._check_ready()
        if not cookie or self._busy:
            return
        self._busy = True
        self.pages, self.cursors, self.page = {}, [""], 0
        threading.Thread(target=self._worker_all, args=(self.item_id, cookie), daemon=True).start()

    def _worker_all(self, item_id: int, cookie: str) -> None:
        cursor, n, total = "", 0, 0
        pages: dict[int, list[dict]] = {}
        try:
            while n < MAX_PAGES_ALL:
                rows, cursor = self._load_page(item_id, cookie, cursor)
                pages[n] = rows
                total += len(rows)
                n += 1
                safe_after(self, lambda t=total, k=n: self.info_lbl.configure(
                    text=f"Carregando... {t} donos ({k} páginas)"))
                if not cursor:
                    break
        except Exception as e:  # noqa: BLE001
            msg = str(e)
            if not pages:
                safe_after(self, lambda: self._fail(msg))
                return
            safe_after(self, lambda: self.info_lbl.configure(text=f"⚠ Parou em {total} donos: {msg}"))
        safe_after(self, lambda: self._done_all(item_id, pages, cursor))

    def _done_all(self, item_id: int, pages: dict[int, list[dict]], cursor: str) -> None:
        self._busy = False
        if item_id != self.item_id:
            return
        self.pages = pages
        self.next_cursor = ""
        rows = [r for k in sorted(pages) for r in pages[k]]
        note = "" if not cursor else f" (limitado a {MAX_PAGES_ALL * 100})"
        self._render(rows, f"Todos: {len(rows)} donos{note}")

    # ------------------------------------------------------------------
    def _render(self, rows: list[dict], label: str) -> None:
        self._clear()
        for r in rows:
            self.tree.insert("", "end", values=[r[f] for f in FIELDS])
        self.page_lbl.configure(text=label)
        self.info_lbl.configure(text=f"Item {self.item_id}: {len(rows)} donos exibidos.")

    def _clear(self) -> None:
        for i in self.tree.get_children():
            self.tree.delete(i)

    def export_csv(self) -> None:
        rows = [r for k in sorted(self.pages) for r in self.pages[k]]
        if not rows:
            messagebox.showinfo("Exportar", "Nada para exportar. Carregue os donos primeiro.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", initialdir=str(export_dir()),
            initialfile=f"donos_{self.item_id}.csv", filetypes=[("CSV", "*.csv")],
        )
        if not path:
            return
        try:
            export_csv(path, rows, fieldnames=FIELDS)
            messagebox.showinfo("Exportar", f"{len(rows)} donos salvos em:\n{path}")
        except Exception as e:  # noqa: BLE001
            messagebox.showerror("Exportar", f"Falha: {e}")
