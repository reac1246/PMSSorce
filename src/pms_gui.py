import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os

def run_gui():
    root = tk.Tk()
    root.title("PMS - Project Management Settings")
    root.geometry("600x500")
    
    # Main Frame
    main_frame = ttk.Frame(root, padding="20")
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Title Label
    title_label = ttk.Label(main_frame, text="PMS Configuration", font=("Helvetica", 16, "bold"))
    title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

    # Configuration Fields
    # Project Name
    ttk.Label(main_frame, text="Project Name:").grid(row=1, column=0, sticky=tk.W, pady=5)
    name_entry = ttk.Entry(main_frame, width=40)
    name_entry.grid(row=1, column=1, columnspan=2, sticky=tk.W, pady=5)

    # Language
    ttk.Label(main_frame, text="Language:").grid(row=2, column=0, sticky=tk.W, pady=5)
    lang_entry = ttk.Entry(main_frame, width=20)
    lang_entry.grid(row=2, column=1, sticky=tk.W, pady=5)

    # Compile Checkbox
    compile_var = tk.BooleanVar()
    ttk.Checkbutton(main_frame, text="Package with Compiling", variable=compile_var).grid(row=3, column=1, sticky=tk.W, pady=5)

    # Zip Target
    ttk.Label(main_frame, text="Zip Target:").grid(row=4, column=0, sticky=tk.W, pady=5)
    zip_var = tk.StringVar(value="src")
    ttk.Radiobutton(main_frame, text="src directory", variable=zip_var, value="src").grid(row=4, column=1, sticky=tk.W, pady=5)
    ttk.Radiobutton(main_frame, text="compiled directory", variable=zip_var, value="compiled").grid(row=5, column=1, sticky=tk.W, pady=5)

    # Dev Directory
    ttk.Label(main_frame, text="Dev Directory:").grid(row=6, column=0, sticky=tk.W, pady=5)
    dev_path_var = tk.StringVar()
    ttk.Entry(main_frame, textvariable=dev_path_var, width=40).grid(row=6, column=1, sticky=tk.W, pady=5)
    
    def browse_dir():
        d = filedialog.askdirectory()
        if d:
            dev_path_var.set(d)
    
    ttk.Button(main_frame, text="Browse...", command=browse_dir).grid(row=6, column=2, padx=5)

    # Save button action
    def save_settings():
        if not name_entry.get() or not dev_path_var.get():
            messagebox.showerror("Error", "Required fields are missing.")
            return
            
        config_data = {
            "ProjectName": name_entry.get(),
            "Language": lang_entry.get(),
            "CompileOnPkg": compile_var.get(),
            "ZipTarget": zip_var.get(),
            "DevelopmentDir": dev_path_var.get()
        }
        
        path = os.path.join(dev_path_var.get(), "infomation.psfl")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("Success", f"Complete! Saved!\n\nPath: {path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")

    ttk.Button(main_frame, text="Save Settings", command=save_settings).grid(row=7, column=1, pady=10)

    # Action Buttons Frame
    action_frame = ttk.LabelFrame(main_frame, text="Actions (Launch CLI)", padding="10")
    action_frame.grid(row=8, column=0, columnspan=3, sticky=tk.W+tk.E, pady=10)

    def run_cmd(cmd):
        os.system(f"start cmd /k {cmd}")

    ttk.Button(action_frame, text="Upload", command=lambda: run_cmd("PMS_syns_setup")).grid(row=0, column=0, padx=5, pady=5)
    ttk.Button(action_frame, text="Syns", command=lambda: run_cmd("PMS_syns")).grid(row=0, column=1, padx=5, pady=5)
    ttk.Button(action_frame, text="Download", command=lambda: run_cmd("PMS_syns_join")).grid(row=0, column=2, padx=5, pady=5)
    ttk.Button(action_frame, text="Build", command=lambda: run_cmd("PMS_pkg")).grid(row=1, column=0, padx=5, pady=5)
    ttk.Button(action_frame, text="Zip", command=lambda: run_cmd("PMS_zip")).grid(row=1, column=1, padx=5, pady=5)
    ttk.Button(action_frame, text="Edit", command=lambda: run_cmd("PMS_Edit")).grid(row=1, column=2, padx=5, pady=5)

    root.mainloop()

if __name__ == "__main__":
    run_gui()
