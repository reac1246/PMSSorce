import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import sys
import threading
import requests

# ---------------------------------------------------------------------------
# Global config path
# ---------------------------------------------------------------------------
GLOBAL_CONFIG_PATH = r"C:\PMS\System\pms_global.json"

HEADERS = {
    'User-Agent': 'PMSPublisher/1.0'
}


def get_global_config():
    if os.path.exists(GLOBAL_CONFIG_PATH):
        try:
            with open(GLOBAL_CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


# ---------------------------------------------------------------------------
# Styling constants
# ---------------------------------------------------------------------------
BG       = "#0f172a"
CARD     = "#1e293b"
SURFACE  = "#263145"
PRIMARY  = "#6366f1"
SUCCESS  = "#10b981"
DANGER   = "#ef4444"
TEXT     = "#f8fafc"
MUTED    = "#94a3b8"
BORDER   = "#334155"

FONT_FAMILY = "Segoe UI"
FONT_NORMAL = (FONT_FAMILY, 10)
FONT_BOLD   = (FONT_FAMILY, 10, "bold")
FONT_TITLE  = (FONT_FAMILY, 18, "bold")
FONT_LABEL  = (FONT_FAMILY, 9)
FONT_MONO   = ("Consolas", 9)


# ---------------------------------------------------------------------------
# Custom Widgets
# ---------------------------------------------------------------------------
class DarkEntry(tk.Entry):
    def __init__(self, master, **kw):
        kw.setdefault("bg", SURFACE)
        kw.setdefault("fg", TEXT)
        kw.setdefault("insertbackground", TEXT)
        kw.setdefault("relief", "flat")
        kw.setdefault("highlightthickness", 1)
        kw.setdefault("highlightbackground", BORDER)
        kw.setdefault("highlightcolor", PRIMARY)
        kw.setdefault("font", FONT_NORMAL)
        super().__init__(master, **kw)


class DarkButton(tk.Button):
    def __init__(self, master, accent=False, danger=False, **kw):
        bg = DANGER if danger else (PRIMARY if accent else SURFACE)
        kw.setdefault("bg", bg)
        kw.setdefault("fg", TEXT)
        kw.setdefault("relief", "flat")
        kw.setdefault("font", FONT_BOLD)
        kw.setdefault("cursor", "hand2")
        kw.setdefault("activebackground", PRIMARY)
        kw.setdefault("activeforeground", TEXT)
        kw.setdefault("padx", 16)
        kw.setdefault("pady", 8)
        super().__init__(master, **kw)
        self._bg = bg
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, _):
        self.config(bg=PRIMARY)

    def _on_leave(self, _):
        self.config(bg=self._bg)


class LogBox(tk.Frame):
    def __init__(self, master, **kw):
        super().__init__(master, bg=CARD, **kw)
        self._text = tk.Text(
            self,
            bg=CARD, fg=TEXT, font=FONT_MONO,
            relief="flat", state="disabled",
            wrap="word", height=10,
            insertbackground=TEXT,
            selectbackground=PRIMARY,
        )
        sb = tk.Scrollbar(self, orient="vertical", command=self._text.yview)
        self._text.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._text.pack(side="left", fill="both", expand=True)

        # colour tags
        self._text.tag_configure("ok",   foreground=SUCCESS)
        self._text.tag_configure("err",  foreground=DANGER)
        self._text.tag_configure("info", foreground=MUTED)
        self._text.tag_configure("head", foreground=PRIMARY, font=(FONT_FAMILY, 9, "bold"))

    def append(self, msg: str, tag: str = "info"):
        self._text.config(state="normal")
        self._text.insert("end", msg + "\n", tag)
        self._text.see("end")
        self._text.config(state="disabled")

    def clear(self):
        self._text.config(state="normal")
        self._text.delete("1.0", "end")
        self._text.config(state="disabled")


# ---------------------------------------------------------------------------
# Main Application
# ---------------------------------------------------------------------------
class PublisherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PMS Publisher — アップデート配信ツール")
        self.geometry("680x680")
        self.resizable(False, False)
        self.configure(bg=BG)
        self._publishing = False

        # Load saved credentials from global config
        self._global_cfg = get_global_config()

        self._build_ui()
        self._auto_fill()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------
    def _build_ui(self):
        # ── Title bar ──────────────────────────────────────────────────
        title_bar = tk.Frame(self, bg=CARD, height=64)
        title_bar.pack(fill="x")
        title_bar.pack_propagate(False)

        tk.Label(
            title_bar,
            text="📦  PMS Publisher",
            font=FONT_TITLE,
            bg=CARD, fg=TEXT,
            padx=24,
        ).pack(side="left", anchor="w")

        tk.Label(
            title_bar,
            text="アップデート配信ツール",
            font=FONT_LABEL,
            bg=CARD, fg=MUTED,
        ).pack(side="left", anchor="sw", pady=(20, 4))

        # ── Main canvas (scrollable) ────────────────────────────────────
        outer = tk.Frame(self, bg=BG)
        outer.pack(fill="both", expand=True, padx=24, pady=16)

        # ── Section: Server & Auth ─────────────────────────────────────
        self._section(outer, "🔗  サーバー & 認証")

        grid = tk.Frame(outer, bg=BG)
        grid.pack(fill="x")
        grid.columnconfigure(1, weight=1)

        self.api_var   = self._row(grid, 0, "APIサーバー URL",  "https://your-server.com/PMS/api.php")
        self.id_var    = self._row(grid, 1, "Admin ID")
        self.pw_var    = self._row(grid, 2, "Admin Password", show="*")
        self.pin_var   = self._row(grid, 3, "Security PIN",   show="*")

        # ── Section: Update Info ───────────────────────────────────────
        self._section(outer, "🏷  アップデート情報")

        grid2 = tk.Frame(outer, bg=BG)
        grid2.pack(fill="x")
        grid2.columnconfigure(1, weight=1)

        self.ver_var   = self._row(grid2, 0, "バージョン番号", "例: 1.0.7")
        self.notes_var = self._row(grid2, 1, "リリースノート", "例: バグ修正、機能追加など")

        # ── Section: EXE file ─────────────────────────────────────────
        self._section(outer, "📁  配信する EXEファイル")

        file_frame = tk.Frame(outer, bg=BG)
        file_frame.pack(fill="x")
        file_frame.columnconfigure(0, weight=1)

        self.exe_var = tk.StringVar()
        entry_row = tk.Frame(file_frame, bg=BG)
        entry_row.pack(fill="x", pady=(0, 6))

        self._exe_entry = DarkEntry(entry_row, textvariable=self.exe_var, width=55)
        self._exe_entry.pack(side="left", fill="x", expand=True)

        DarkButton(
            entry_row,
            text="参照…",
            command=self._browse_exe,
        ).pack(side="left", padx=(6, 0))

        DarkButton(
            file_frame,
            text="🔍  dist/ から自動検索",
            command=self._auto_find_exe,
        ).pack(anchor="w")

        # ── Publish button ─────────────────────────────────────────────
        btn_frame = tk.Frame(outer, bg=BG)
        btn_frame.pack(fill="x", pady=(20, 0))

        self._publish_btn = DarkButton(
            btn_frame,
            text="🚀  アップデートを配信する",
            accent=True,
            command=self._start_publish,
            pady=12,
        )
        self._publish_btn.pack(fill="x")

        # ── Progress ───────────────────────────────────────────────────
        self._progress = ttk.Progressbar(outer, mode="indeterminate")
        self._progress.pack(fill="x", pady=(8, 0))

        # ── Log ────────────────────────────────────────────────────────
        self._section(outer, "📋  ログ")

        self._log = LogBox(outer)
        self._log.pack(fill="both", expand=True)

        log_btns = tk.Frame(outer, bg=BG)
        log_btns.pack(fill="x", pady=(4, 0))
        DarkButton(log_btns, text="ログをクリア", command=self._log.clear).pack(side="right")

    # ------------------------------------------------------------------
    # Helper builders
    # ------------------------------------------------------------------
    def _section(self, parent, text: str):
        f = tk.Frame(parent, bg=BG)
        f.pack(fill="x", pady=(14, 6))
        tk.Label(f, text=text, font=FONT_BOLD, bg=BG, fg=PRIMARY).pack(side="left")
        tk.Frame(f, bg=BORDER, height=1).pack(side="left", fill="x", expand=True, padx=(8, 0), pady=6)

    def _row(self, grid, row: int, label: str, placeholder: str = "", show: str = ""):
        tk.Label(
            grid,
            text=label + " :",
            font=FONT_LABEL,
            bg=BG, fg=MUTED,
            anchor="e",
            width=18,
        ).grid(row=row, column=0, sticky="e", pady=5, padx=(0, 8))

        var = tk.StringVar()
        entry = DarkEntry(grid, textvariable=var, show=show)
        entry.grid(row=row, column=1, sticky="ew", pady=5)

        if placeholder and not show:
            # faint placeholder behaviour
            entry.config(fg=MUTED)
            entry.insert(0, placeholder)

            def _focus_in(e, ent=entry, ph=placeholder, v=var):
                if ent.get() == ph:
                    ent.delete(0, "end")
                    ent.config(fg=TEXT)

            def _focus_out(e, ent=entry, ph=placeholder, v=var):
                if not ent.get():
                    ent.insert(0, ph)
                    ent.config(fg=MUTED)

            entry.bind("<FocusIn>",  _focus_in)
            entry.bind("<FocusOut>", _focus_out)

        return var

    # ------------------------------------------------------------------
    # Auto-fill from global config
    # ------------------------------------------------------------------
    def _auto_fill(self):
        api = self._global_cfg.get("ApiServer", "")
        if api:
            self.api_var.set(api)
            self._log.append(f"グローバル設定からAPIサーバーを読み込みました: {api}", "ok")
        else:
            self._log.append("グローバル設定 (pms_global.json) が見つかりませんでした。手動で入力してください。", "info")

    # ------------------------------------------------------------------
    # File picker / auto-detect
    # ------------------------------------------------------------------
    def _browse_exe(self):
        path = filedialog.askopenfilename(
            title="配信する EXEファイルを選択",
            filetypes=[("実行ファイル", "*.exe"), ("すべてのファイル", "*.*")]
        )
        if path:
            self.exe_var.set(path)

    def _auto_find_exe(self):
        """dist/ から PMS_Setup.exe を自動探索。"""
        # スクリプト or EXEのディレクトリからの相対パス
        base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        candidates = [
            os.path.join(base, "..", "dist", "PMS_Setup.exe"),
            os.path.join(base, "dist", "PMS_Setup.exe"),
            r"C:\PMS\dist\PMS_Setup.exe",
        ]
        for c in candidates:
            norm = os.path.normpath(c)
            if os.path.exists(norm):
                self.exe_var.set(norm)
                self._log.append(f"EXEを自動検出しました: {norm}", "ok")
                return
        # フォールバック: ユーザーに選択させる
        self._log.append("自動検出できませんでした。手動でファイルを選択してください。", "err")
        self._browse_exe()

    # ------------------------------------------------------------------
    # Publish
    # ------------------------------------------------------------------
    def _start_publish(self):
        if self._publishing:
            return

        api    = self.api_var.get().strip()
        adm_id = self.id_var.get().strip()
        adm_pw = self.pw_var.get().strip()
        adm_pin = self.pin_var.get().strip()
        version = self.ver_var.get().strip()
        notes   = self.notes_var.get().strip()
        exe_path = self.exe_var.get().strip()

        # ── Validation ─────────────────────────────────────────────────
        ph_api   = "https://your-server.com/PMS/api.php"
        ph_ver   = "例: 1.0.7"
        ph_notes = "例: バグ修正、機能追加など"

        api     = "" if api     == ph_api   else api
        if api and not api.startswith("http"):
            api = "https://" + api
        version = "" if version == ph_ver   else version
        notes   = "" if notes   == ph_notes else notes

        errors = []
        if not api:      errors.append("APIサーバー URLが未入力です。")
        if not adm_id:   errors.append("Admin IDが未入力です。")
        if not adm_pw:   errors.append("Passwordが未入力です。")
        if not adm_pin:  errors.append("Security PINが未入力です。")
        if not version:  errors.append("バージョン番号が未入力です。")
        if not exe_path: errors.append("EXEファイルが選択されていません。")
        elif not os.path.exists(exe_path):
            errors.append(f"EXEファイルが見つかりません:\n{exe_path}")

        if errors:
            messagebox.showerror("入力エラー", "\n".join(errors))
            return

        self._publishing = True
        self._publish_btn.config(state="disabled", text="配信中…")
        self._progress.start(12)
        self._log.clear()
        self._log.append("=" * 50, "head")
        self._log.append(f"  PMS Publisher — 配信開始", "head")
        self._log.append("=" * 50, "head")

        thread = threading.Thread(
            target=self._do_publish,
            args=(api, adm_id, adm_pw, adm_pin, version, notes, exe_path),
            daemon=True,
        )
        thread.start()

    def _do_publish(self, api, adm_id, adm_pw, adm_pin, version, notes, exe_path):
        try:
            self._log.append(f"\n▶  サーバーへ接続中... {api}", "info")

            exe_size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            self._log.append(f"▶  ファイル: {os.path.basename(exe_path)}  ({exe_size_mb:.2f} MB)", "info")
            self._log.append(f"▶  バージョン: {version}", "info")

            with open(exe_path, "rb") as f:
                response = requests.post(
                    api,
                    params={"action": "distribute_update"},
                    data={
                        "admin_id":      adm_id,
                        "admin_pw":      adm_pw,
                        "admin_pin":     adm_pin,
                        "version":       version,
                        "release_notes": notes,
                    },
                    files={"setup_exe": (os.path.basename(exe_path), f, "application/octet-stream")},
                    headers=HEADERS,
                    timeout=120,
                )

            if response.status_code == 200:
                try:
                    result = response.json()
                except Exception:
                    result = {"status": "ok", "message": response.text}

                if result.get("status") == "ok":
                    self._log.append(f"\n✅  配信完了！", "ok")
                    self._log.append(f"   バージョン : {result.get('version', version)}", "ok")
                    dl_url = result.get("download_url", "")
                    if dl_url:
                        self._log.append(f"   DL URL    : {dl_url}", "ok")
                    self.after(0, lambda: messagebox.showinfo(
                        "配信完了",
                        f"✅ バージョン {version} の配信が完了しました！\n\nサーバー: {api}"
                    ))
                else:
                    msg = result.get("message", "Unknown error")
                    self._log.append(f"\n❌  サーバーエラー: {msg}", "err")
                    self.after(0, lambda m=msg: messagebox.showerror("配信失敗", f"サーバーからエラーが返りました:\n{m}"))
            elif response.status_code == 401:
                self._log.append(f"\n❌  認証失敗 (401): ID/PW/PINを確認してください。", "err")
                self.after(0, lambda: messagebox.showerror("認証エラー", "Admin ID / Password / PIN が正しくありません。"))
            elif response.status_code == 403:
                self._log.append(f"\n❌  アクセス拒否 (403)", "err")
                self.after(0, lambda: messagebox.showerror("アクセス拒否", "このアカウントでは配信権限がありません。"))
            else:
                body = response.text[:300]
                self._log.append(f"\n❌  HTTP {response.status_code}: {body}", "err")
                self.after(0, lambda c=response.status_code: messagebox.showerror(
                    "配信失敗", f"HTTPエラー {c} が発生しました。\nAPIサーバーのURLを確認してください。"
                ))

        except requests.exceptions.ConnectionError:
            self._log.append(f"\n❌  接続エラー: サーバーに到達できません。", "err")
            self.after(0, lambda: messagebox.showerror("接続エラー", "サーバーに接続できませんでした。\nURLとネットワークを確認してください。"))
        except requests.exceptions.Timeout:
            self._log.append(f"\n❌  タイムアウト: アップロードに時間がかかりすぎました。", "err")
            self.after(0, lambda: messagebox.showerror("タイムアウト", "アップロードがタイムアウトしました。\nファイルサイズやネットワーク速度を確認してください。"))
        except Exception as e:
            self._log.append(f"\n❌  予期せぬエラー: {e}", "err")
            self.after(0, lambda err=str(e): messagebox.showerror("エラー", f"予期せぬエラーが発生しました:\n{err}"))
        finally:
            self.after(0, self._finish_publish)

    def _finish_publish(self):
        self._publishing = False
        self._progress.stop()
        self._publish_btn.config(state="normal", text="🚀  アップデートを配信する")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app = PublisherApp()
    app.mainloop()
