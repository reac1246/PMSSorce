import os
import sys
import shutil
import ctypes
import winreg
import json
import tkinter as tk
from tkinter import ttk, messagebox

def is_admin():
    try:
        # Check if the process has administrative privileges
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except AttributeError:
        # Fallback if windll is not available
        return False

def add_to_path(new_path):
    try:
        registry_key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment',
            0,
            winreg.KEY_ALL_ACCESS
        )
        try:
            current_path, reg_type = winreg.QueryValueEx(registry_key, 'Path')
            if new_path.lower() not in current_path.lower():
                new_full_path = current_path.rstrip(';') + ';' + new_path
                winreg.SetValueEx(registry_key, 'Path', 0, winreg.REG_EXPAND_SZ, new_full_path)
                
                # Notify system of environment change
                HWND_BROADCAST = 0xFFFF
                WM_SETTINGCHANGE = 0x001A
                ctypes.windll.user32.SendMessageTimeoutW(
                    HWND_BROADCAST, WM_SETTINGCHANGE, 0, 'Environment', 0x02, 1000, None
                )
                return True, "Successfully added to PATH."
            return True, "Path already registered."
        finally:
            winreg.CloseKey(registry_key)
    except Exception as e:
        return False, str(e)

def setup_files():
    try:
        # PyInstaller uses _MEIPASS for bundled resources
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        target_base = r"C:\PMS\System"
        
        src_bin = os.path.join(base_path, "bin")
        src_src = os.path.join(base_path, "src")
        
        if not os.path.exists(target_base):
            os.makedirs(target_base)
            
        # Copy bin directory
        if os.path.exists(src_bin):
            dst_bin = os.path.join(target_base, "bin")
            if os.path.exists(dst_bin):
                shutil.rmtree(dst_bin)
            shutil.copytree(src_bin, dst_bin)
            
        # Copy src directory
        if os.path.exists(src_src):
            dst_src = os.path.join(target_base, "src")
            if os.path.exists(dst_src):
                shutil.rmtree(dst_src)
            shutil.copytree(src_src, dst_src)
            
        # Generate .bat wrappers for commands in bin
        dst_bin = os.path.join(target_base, "bin")
        if not os.path.exists(dst_bin):
            os.makedirs(dst_bin)
            
        commands = [
            "PMS_Start", "PMS_Edit", "PMS_gui", "PMS_pkg", "PMS_zip",
            "PMS_syns_setup", "PMS_syns_join", "PMS_syns", "PMS_syns_edit", "PMS_Update"
        ]
        for cmd in commands:
            bat_path = os.path.join(dst_bin, f"{cmd}.bat")
            with open(bat_path, "w", encoding="utf-8") as f:
                f.write(f"@echo off\r\n\"{os.path.join(dst_bin, 'PMS.exe')}\" {cmd} %*\r\n")
            
        # Copy version.txt if exists
        src_ver = os.path.join(base_path, "version.txt")
        if os.path.exists(src_ver):
            shutil.copy2(src_ver, os.path.join(target_base, "version.txt"))
            
        return True, "Files extracted."
    except Exception as e:
        # Save error to a log file next to the installer for debugging
        log_path = os.path.join(os.path.dirname(sys.executable), "Installer_Error.log")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"Extraction failed: {str(e)}")
        return False, str(e)

class InstallerUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PMS Setup")
        self.root.geometry("450x350")
        
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="PMS - Project Management System", font=("Helvetica", 12, "bold")).pack(pady=10)
        
        ttk.Label(main_frame, text="Language / 言語:").pack(pady=(10, 2))
        self.lang_var = tk.StringVar(value="日本語")
        lang_cb = ttk.Combobox(main_frame, textvariable=self.lang_var, values=["日本語", "English"], state="readonly", width=30)
        lang_cb.pack(pady=2)

        ttk.Label(main_frame, text="Default API Server:").pack(pady=(10, 2))
        self.api_var = tk.StringVar(value="")
        api_cb = ttk.Combobox(main_frame, textvariable=self.api_var, values=[], width=40)
        api_cb.pack(pady=2)
        ttk.Label(
            main_frame,
            text="⚠ 例: https://yourdomain.com/PMS/api.php\n※ 末尾まで /api.php と入力してください",
            foreground="#e67e22",
            font=("Helvetica", 8),
            justify="center"
        ).pack(pady=(0, 2))

        self.btn = ttk.Button(main_frame, text="Install to C:\\PMS\\System", command=self.do_install)
        self.btn.pack(pady=20)
        
        self.status = tk.StringVar(value="Ready")
        ttk.Label(main_frame, textvariable=self.status).pack()

    def do_install(self):
        if not is_admin():
            messagebox.showwarning("Admin Required", "Please run this installer as administrator.\n管理者として実行してください。")
            return

        self.status.set("Extracting files...")
        self.root.update()
        
        success, msg = setup_files()
        if not success:
            messagebox.showerror("Error", f"Failed to extract files: {msg}\nCheck Installer_Error.log for details.")
            return
            
        self.status.set("Setting up PATH...")
        self.root.update()
        
        path_success, path_msg = add_to_path(r"C:\PMS\System\bin")
        if not path_success:
            messagebox.showerror("Error", f"Failed to set PATH: {path_msg}")
            return

        # Save global configuration
        try:
            global_config = {
                "Language": self.lang_var.get(),
                "ApiServer": self.api_var.get()
            }
            with open(r"C:\PMS\System\pms_global.json", "w", encoding="utf-8") as f:
                json.dump(global_config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print("Warning: Failed to save global config:", e)
            
        messagebox.showinfo("Success", "Installation Complete!\nPlease restart your terminal.\nインストールが完了しました。")
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = InstallerUI(root)
    root.mainloop()
