import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os

def run_gui():
    root = tk.Tk()
    root.title("PMS - プロジェクト管理設定")
    root.geometry("600x500")
    
    # Main Frame
    main_frame = ttk.Frame(root, padding="20")
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Title Label
    title_label = ttk.Label(main_frame, text="PMS 設定", font=("Helvetica", 16, "bold"))
    title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

    # Configuration Fields
    # Project Name
    ttk.Label(main_frame, text="プロジェクト名:").grid(row=1, column=0, sticky=tk.W, pady=5)
    name_entry = ttk.Entry(main_frame, width=40)
    name_entry.grid(row=1, column=1, columnspan=2, sticky=tk.W, pady=5)

    # Language
    ttk.Label(main_frame, text="言語 (Python/Dotnet等):").grid(row=2, column=0, sticky=tk.W, pady=5)
    lang_entry = ttk.Entry(main_frame, width=20)
    lang_entry.grid(row=2, column=1, sticky=tk.W, pady=5)

    # Compile Checkbox
    compile_var = tk.BooleanVar()
    ttk.Checkbutton(main_frame, text="ビルドしてからパッケージ化する", variable=compile_var).grid(row=3, column=1, sticky=tk.W, pady=5)

    single_var = tk.BooleanVar()
    ttk.Checkbutton(main_frame, text="単一ファイル化(OneFile)", variable=single_var).grid(row=3, column=2, sticky=tk.W, pady=5)

    # Zip Target
    ttk.Label(main_frame, text="圧縮対象(Zip Target):").grid(row=4, column=0, sticky=tk.W, pady=5)
    zip_var = tk.StringVar(value="src")
    ttk.Entry(main_frame, textvariable=zip_var, width=40).grid(row=4, column=1, sticky=tk.W, pady=5)
    
    def browse_zip_target():
        d = filedialog.askdirectory()
        if d:
            zip_var.set(d)
    
    ttk.Button(main_frame, text="参照...", command=browse_zip_target).grid(row=4, column=2, padx=5)

    # Dev Directory
    ttk.Label(main_frame, text="開発ディレクトリ:").grid(row=5, column=0, sticky=tk.W, pady=5)
    dev_path_var = tk.StringVar()
    ttk.Entry(main_frame, textvariable=dev_path_var, width=40).grid(row=5, column=1, sticky=tk.W, pady=5)
    
    def browse_dev_dir():
        d = filedialog.askdirectory()
        if d:
            dev_path_var.set(d)
    
    ttk.Button(main_frame, text="参照...", command=browse_dev_dir).grid(row=5, column=2, padx=5)

    # Save button action
    def save_settings():
        if not name_entry.get() or not dev_path_var.get():
            messagebox.showerror("エラー", "必須項目が入力されていません。")
            return
            
        config_data = {
            "ProjectName": name_entry.get(),
            "Language": lang_entry.get(),
            "CompileOnPkg": compile_var.get(),
            "IsSingleFile": single_var.get(),
            "ZipTarget": zip_var.get(),
            "DevelopmentDir": dev_path_var.get()
        }
        
        path = os.path.join(dev_path_var.get(), "infomation.psfl")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("成功", f"設定を保存しました！\n\nパス: {path}")
        except Exception as e:
            messagebox.showerror("エラー", f"保存に失敗しました: {e}")

    ttk.Button(main_frame, text="設定を保存", command=save_settings).grid(row=6, column=1, pady=10)

    # Action Buttons Frame
    action_frame = ttk.LabelFrame(main_frame, text="アクション (CLIを起動)", padding="10")
    action_frame.grid(row=7, column=0, columnspan=3, sticky=tk.W+tk.E, pady=10)

    def run_cmd(cmd):
        os.system(f"start cmd /k {cmd}")

    ttk.Button(action_frame, text="初期アップロード", command=lambda: run_cmd("PMS_syns_setup")).grid(row=0, column=0, padx=5, pady=5)
    ttk.Button(action_frame, text="同期(Sync)", command=lambda: run_cmd("PMS_syns")).grid(row=0, column=1, padx=5, pady=5)
    ttk.Button(action_frame, text="ダウンロード参加", command=lambda: run_cmd("PMS_syns_join")).grid(row=0, column=2, padx=5, pady=5)
    ttk.Button(action_frame, text="ビルド＆Zip", command=lambda: run_cmd("PMS_pkg")).grid(row=1, column=0, padx=5, pady=5)
    ttk.Button(action_frame, text="Zip圧縮のみ", command=lambda: run_cmd("PMS_zip")).grid(row=1, column=1, padx=5, pady=5)
    ttk.Button(action_frame, text="設定編集", command=lambda: run_cmd("PMS_Edit")).grid(row=1, column=2, padx=5, pady=5)
    ttk.Button(action_frame, text="アップデート確認", command=lambda: run_cmd("PMS_Update")).grid(row=2, column=0, padx=5, pady=5)

    root.mainloop()

if __name__ == "__main__":
    run_gui()
