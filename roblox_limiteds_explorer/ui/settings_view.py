"""Aba "Configurações": tema, cookie, alertas, cache."""
from __future__ import annotations

from tkinter import messagebox

import customtkinter as ctk

from core import cache
from core.config import config
from core.watcher import watcher


class SettingsView(ctk.CTkFrame):
    def __init__(self, master, app) -> None:
        super().__init__(master, fg_color="transparent")
        self.app = app

        box = ctk.CTkFrame(self)
        box.pack(fill="x", padx=20, pady=20)
        box.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(box, text="Tema:").grid(row=0, column=0, sticky="w", padx=8, pady=8)
        self.theme_var = ctk.StringVar(value=config.get("theme", "dark"))
        self.theme_menu = ctk.CTkOptionMenu(box, values=["dark", "light"], variable=self.theme_var,
                                            command=self.app.set_theme)
        self.theme_menu.grid(row=0, column=1, sticky="w", padx=8, pady=8)

        ctk.CTkLabel(box, text="Cookie .ROBLOSECURITY (opcional):").grid(row=1, column=0, sticky="w", padx=8, pady=8)
        self.cookie_entry = ctk.CTkEntry(box, show="•")
        self.cookie_entry.grid(row=1, column=1, sticky="ew", padx=8, pady=8)
        self.cookie_entry.insert(0, config.get_cookie())

        ctk.CTkLabel(
            box, justify="left", wraplength=760, text_color="#f59e0b",
            text=("⚠ Nunca compartilhe este cookie: ele dá acesso total à sua conta. Use, de preferência, "
                  "uma conta alternativa. Ele fica guardado no cofre de credenciais do Windows (ou no "
                  "config.json se o cofre não estiver disponível) e só é enviado ao Roblox "
                  "(listar donos / baixar assets protegidos)."),
        ).grid(row=2, column=0, columnspan=2, sticky="w", padx=8, pady=(0, 8))

        ctk.CTkButton(box, text="Salvar cookie", command=self._save_cookie).grid(row=3, column=0, padx=8, pady=8, sticky="w")
        ctk.CTkButton(box, text="Limpar cookie", command=self._clear_cookie).grid(row=3, column=1, padx=8, pady=8, sticky="w")

        ctk.CTkLabel(box, text="Verificar favoritos a cada (min):").grid(row=4, column=0, sticky="w", padx=8, pady=8)
        self.interval_entry = ctk.CTkEntry(box, width=100)
        self.interval_entry.grid(row=4, column=1, sticky="w", padx=8, pady=8)
        self.interval_entry.insert(0, str(config.get("watch_interval_min", 15)))

        self.watch_var = ctk.BooleanVar(value=bool(config.get("watch_enabled")))
        ctk.CTkSwitch(box, text="Ativar alertas em segundo plano", variable=self.watch_var,
                      command=self._toggle_watch).grid(row=5, column=0, columnspan=2, sticky="w", padx=8, pady=8)

        self.notify_var = ctk.BooleanVar(value=bool(config.get("notify_on_change", True)))
        ctk.CTkSwitch(box, text="Notificar mudanças de RAP/preço", variable=self.notify_var,
                      command=self._toggle_notify).grid(row=6, column=0, columnspan=2, sticky="w", padx=8, pady=8)

        ctk.CTkButton(box, text="Salvar intervalo", command=self._save_interval).grid(row=7, column=0, padx=8, pady=12, sticky="w")
        ctk.CTkButton(box, text="Limpar cache", command=self._clear_cache).grid(row=7, column=1, padx=8, pady=12, sticky="w")

    # ------------------------------------------------------------------
    def _save_cookie(self) -> None:
        secure = config.set_cookie(self.cookie_entry.get())
        where = "no cofre de credenciais do Windows" if secure else "no config.json (cofre indisponível)"
        messagebox.showinfo("Configurações", f"Cookie salvo {where}.")

    def _clear_cookie(self) -> None:
        self.cookie_entry.delete(0, "end")
        config.set_cookie("")
        messagebox.showinfo("Configurações", "Cookie removido.")

    def _save_interval(self) -> None:
        try:
            v = max(1, int(self.interval_entry.get() or 15))
        except ValueError:
            v = 15
        self.interval_entry.delete(0, "end")
        self.interval_entry.insert(0, str(v))
        config.set("watch_interval_min", v)
        messagebox.showinfo("Configurações", f"Intervalo salvo: {v} min (vale a partir da próxima verificação).")

    def _toggle_watch(self) -> None:
        enabled = bool(self.watch_var.get())
        config.set("watch_enabled", enabled)
        if enabled:
            watcher.start()
        else:
            watcher.stop()

    def _toggle_notify(self) -> None:
        config.set("notify_on_change", bool(self.notify_var.get()))

    def _clear_cache(self) -> None:
        cache.clear()
        messagebox.showinfo("Configurações", "Cache limpo.")
