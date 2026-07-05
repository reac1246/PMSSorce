import os
import json
import shutil
import tkinter as tk
from tkinter import ttk, messagebox

class PublisherUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PMS Update Publisher")
        self.root.geometry("400x350")
        
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="PMS Update Publisher", font=("Helvetica", 14, "bold")).pack(pady=(0, 15))
        
        # Determine current version from version.txt
        current_version = "1.0.0"
        version_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "version.txt")
        if os.path.exists(version_file):
            with open(version_file, "r", encoding="utf-8") as f:
                current_version = f.read().strip()
                
        # Version
        version_frame = ttk.Frame(main_frame)
        version_frame.pack(fill=tk.X, pady=5)
        ttk.Label(version_frame, text="Version:", width=15).pack(side=tk.LEFT)
        self.version_var = tk.StringVar(value=current_version)
        ttk.Entry(version_frame, textvariable=self.version_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Target SV Directory
        sv_frame = ttk.Frame(main_frame)
        sv_frame.pack(fill=tk.X, pady=5)
        ttk.Label(sv_frame, text="SV Updates Dir:", width=15).pack(side=tk.LEFT)
        self.sv_var = tk.StringVar(value=r"C:\SV\PMS\updates")
        ttk.Entry(sv_frame, textvariable=self.sv_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Release Notes
        ttk.Label(main_frame, text="Release Notes:").pack(anchor=tk.W, pady=(10, 2))
        self.notes_text = tk.Text(main_frame, height=5, width=40)
        self.notes_text.pack(fill=tk.BOTH, expand=True)
        self.notes_text.insert(tk.END, "- Bug fixes and improvements.")
        
        # Publish Button
        self.publish_btn = ttk.Button(main_frame, text="Publish to SV", command=self.do_publish)
        self.publish_btn.pack(pady=15)
        
    def do_publish(self):
        version = self.version_var.get().strip()
        sv_dir = self.sv_var.get().strip()
        notes = self.notes_text.get("1.0", tk.END).strip()
        
        if not version or not sv_dir:
            messagebox.showerror("Error", "Version and SV Directory are required.")
            return
            
        if not os.path.exists(sv_dir):
            try:
                os.makedirs(sv_dir)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create SV directory:\n{e}")
                return
                
        # Source EXE
        root_dir = os.path.dirname(os.path.dirname(__file__))
        src_exe = os.path.join(root_dir, "dist", "PMS_Setup.exe")
        
        if not os.path.exists(src_exe):
            messagebox.showerror("Error", f"PMS_Setup.exe not found at:\n{src_exe}\n\nPlease run build_exes.py first.")
            return
            
        target_exe = os.path.join(sv_dir, "PMS_Setup.exe")
        target_json = os.path.join(sv_dir, "latest.json")
        
        try:
            # Copy EXE
            shutil.copy2(src_exe, target_exe)
            
            # Write JSON
            json_data = {
                "version": version,
                "download_url": "updates/PMS_Setup.exe",
                "release_notes": notes
            }
            with open(target_json, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=4, ensure_ascii=False)
                
            messagebox.showinfo("Success", f"Update v{version} successfully published to SV!\n\nTarget: {sv_dir}")
            self.root.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to publish update:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PublisherUI(root)
    root.mainloop()
