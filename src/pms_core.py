import os
import sys
import json
import zipfile
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
try:
    import pyzipper
except ImportError:
    pyzipper = None
import requests
import random
import string
import shutil
import io

CONFIG_FILENAME = "infomation.psfl"

# Common Headers to avoid 404/Block from some hostings
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def is_secure_mgmt(mgmt_num):
    return mgmt_num.endswith('_Secure')

def select_api_server():
    print("\n Please select a server to upload/join")
    print("1. JMN_Cloud (jmn.cloudfree.jp)")
    print("2. JMN_Fukuoka-Tecno (tec-fuk.f5.si)")
    print("3. Custom User Server")
    choice = input("> ").strip()
    
    if choice == "1":
        return "https://jmn.cloudfree.jp/PMS/api.php"
    elif choice == "2":
        return "https://tec-fuk.f5.si/PMS/api.php"
    else:
        url = input("Please enter the API server URL (https://.../api.php): ").strip()
        if url and not url.startswith("http"):
            url = "https://" + url
        return url

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def select_directory(title="Please select a directory"):
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    path = filedialog.askdirectory(title=title)
    root.destroy()
    return path

def select_multiple_items(title="Please select multiple items"):
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    paths = filedialog.askopenfilenames(title=title)
    root.destroy()
    return list(paths)

def show_help():
    print("="*40)
    print("PMS - Project Management System")
    print("="*40)
    print("Available Commands:")
    print("  PMS_Start      : Create new project configuration")
    print("  PMS_Edit       : Edit project configuration")
    print("  PMS_gui        : Launch GUI configuration window")
    print("  PMS_pkg        : Build and package the project")
    print("  PMS_zip        : Folder compression wizard")
    print("  PMS_syns_setup : Initial setup and upload to sync API server")
    print("  PMS_syns_join  : Join an existing sync project")
    print("  PMS_syns       : Sync with API server (Push/Pull)")
    print("  PMS_syns_edit  : Change management number and settings")
    print("="*40)

def pms_start():
    print("--- PMS_Start: Project Creation Wizard ---")
    project_name = input("Please enter the Project Name: ").strip()
    language = input("Please enter the primary language (e.g., Python, Dotnet): ").strip()
    
    well_known_languages = ["python", "py", "dotnet", "c#", "cpp", "java", "rust", "rs", "cargo"]
    can_compile_auto = language.lower() in well_known_languages
    
    do_compile_pkg = "N"
    if can_compile_auto:
        do_compile_pkg = input(f"Would you like to compile and compress during PMS_pkg? (Y/N): ").strip().upper()
    
    zip_target = "src"
    is_single_file = False
    dev_dir = select_directory("Please select the root directory of the project")

    if not dev_dir:
        print("Error: No directory was selected.")
        return

    if not project_name:
        project_name = os.path.basename(dev_dir)

    config_data = {
        "ProjectName": project_name,
        "Language": language,
        "CompileOnPkg": do_compile_pkg == "Y",
        "ZipTarget": zip_target,
        "IsSingleFile": is_single_file,
        "DevelopmentDir": dev_dir
    }

    config_path = os.path.join(dev_dir, CONFIG_FILENAME)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=4, ensure_ascii=False)
    
    print("\nComplete! Saved!")

def pms_syns_setup():
    print("--- PMS_syns_setup: Sync API Setup ---")
    current_dir = os.getcwd()
    config_path = os.path.join(current_dir, CONFIG_FILENAME)
    config_data = {}
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)

    api_server = select_api_server()
    if not api_server: return

    login_id = input("\nID: ").strip()
    login_pw = input("PW: ").strip()
    
    print("Verifying credentials...")
    try:
        res = requests.post(f"{api_server}?action=verify", json={"login_id": login_id, "login_pw": login_pw}, headers=HEADERS, timeout=5)
        if res.status_code == 200:
            print("Account is valid. Proceeding.")
        else:
            print(f"Error Code: {res.status_code} - {res.text}")
            return
    except Exception as e:
        print(f"Error: Unable to connect to the server. {e}")
        return

    print("Please enter the PMS Management Number (PMS ID)")
    mgmt_prompt = "Enter existing ID starting with 'PMS_', or a new code suffix (leave blank to auto-generate): "
    mgmt_input = input(mgmt_prompt).strip()
    
    if not mgmt_input:
        mgmt_num = "" 
    elif mgmt_input.startswith("PMS_"):
        mgmt_num = mgmt_input
    else:
        mgmt_num = f"PMS_{login_id}_{mgmt_input}"

    project_name = config_data.get("ProjectName", os.path.basename(current_dir))
    zip_name = f"{project_name}_initial.zip"
    zip_path = os.path.join(current_dir, zip_name)
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(current_dir):
                for file in files:
                    if file.endswith(".zip") or file == CONFIG_FILENAME: continue
                    file_p = os.path.join(root, file)
                    arcname = os.path.relpath(file_p, current_dir)
                    zipf.write(file_p, arcname)
        
        print("Uploading to the data server...")
        with open(zip_path, 'rb') as f:
            upload_res = requests.post(
                f"{api_server}?action=setup",
                data={"login_id": login_id, "login_pw": login_pw, "project_name": project_name, "management_number": mgmt_num},
                files={"file": f},
                headers=HEADERS,
                timeout=30
            )
        
        if upload_res.status_code == 200:
            result = upload_res.json()
            mgmt_num = result.get("management_number", mgmt_num)
            print(f"Setup complete. Management Number: {mgmt_num}")
        else:
            print(f"Setup failed: {upload_res.status_code} - {upload_res.text}")
            return
    except Exception as e:
        print(f"Error: {e}")
        return
    finally:
        if os.path.exists(zip_path): os.remove(zip_path)

    config_data.update({"ApiServer": api_server, "LoginID": login_id, "LoginPW": login_pw, "ManagementNumber": mgmt_num})
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=4, ensure_ascii=False)

def pms_syns_edit():
    print("--- PMS_syns_edit: Change Management Number & Settings ---")
    current_dir = os.getcwd()
    config_path = os.path.join(current_dir, CONFIG_FILENAME)
    if not os.path.exists(config_path):
        print("Configuration file not found.")
        return
        
    with open(config_path, "r", encoding="utf-8") as f:
        config_data = json.load(f)
        
    api_server = config_data.get("ApiServer")
    login_id = config_data.get("LoginID")
    login_pw = config_data.get("LoginPW")
    old_mgmt = config_data.get("ManagementNumber")
    
    print(f"Current Management Number: {old_mgmt}")
    new_mgmt = input("Please enter the new Management Number: ").strip()
    if not new_mgmt or new_mgmt == old_mgmt:
        print("No changes made.")
        return
        
    change_key = ""
    old_parts = old_mgmt.split('_')
    new_parts = new_mgmt.split('_')
    if len(old_parts) > 1 and len(new_parts) > 1 and old_parts[1] != new_parts[1]:
        print("Warning: Detected a change in the UserID portion.")
        change_key = input("Please enter the ChangeKey issued from admin.php: ").strip()
        if not change_key:
            print("ChangeKey is required.")
            return

    print("Applying changes to the server...")
    try:
        res = requests.post(f"{api_server}?action=edit", json={
            "login_id": login_id, "login_pw": login_pw,
            "old_management_number": old_mgmt, "new_management_number": new_mgmt,
            "change_key": change_key
        }, headers=HEADERS, timeout=10)
        
        if res.status_code == 200:
            config_data["ManagementNumber"] = new_mgmt
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            print(f"Management number successfully updated to {new_mgmt}.")
        else:
            print(f"Update failed: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"Error: {e}")

def pms_syns_join():
    print("--- PMS_syns_join: Join Project ---")
    api_server = select_api_server()
    if not api_server: return

    login_id = input("Please enter Login ID: ").strip()
    login_pw = input("Please enter Login PW: ").strip()
    mgmt_num = input("Please enter the PMS Management Number to join: ").strip()
    
    auth_params = {"login_id": login_id, "login_pw": login_pw}
    try:
        res = requests.get(f"{api_server}", params={"action": "info", "management_number": mgmt_num, **auth_params}, headers=HEADERS, timeout=5)
        if res.status_code != 200:
            print("Project information not found.")
            return
        info = res.json()
        print(f"Project: {info.get('project_name')} (Ver: {info.get('latest_version')})")
    except Exception as e:
        print(f"Error: {e}"); return

    dev_dir = select_directory("Select destination directory")
    if not dev_dir: return

    print("Downloading...")
    try:
        res = requests.get(f"{api_server}", params={"action": "download", "management_number": mgmt_num, **auth_params}, headers=HEADERS, timeout=60)
        if res.status_code == 200:
            zip_path = os.path.join(dev_dir, "down.zip")
            with open(zip_path, 'wb') as f: f.write(res.content)
            with zipfile.ZipFile(zip_path, 'r') as z: z.extractall(dev_dir)
            os.remove(zip_path)
            
            config_data = {"ApiServer": api_server, "LoginID": login_id, "LoginPW": login_pw, "ManagementNumber": mgmt_num}
            with open(os.path.join(dev_dir, CONFIG_FILENAME), "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            print("Extraction complete.")
    except Exception as e:
        print(f"Error: {e}")

def pms_syns():
    print("--- PMS_syns: Sync with API Server ---")
    current_dir = os.getcwd()
    config_path = os.path.join(current_dir, CONFIG_FILENAME)
    if not os.path.exists(config_path):
        print("Configuration file not found.")
        return
        
    with open(config_path, "r", encoding="utf-8") as f:
        config_data = json.load(f)
        
    api_server = config_data.get("ApiServer")
    login_id = config_data.get("LoginID")
    login_pw = config_data.get("LoginPW")
    mgmt_num = config_data.get("ManagementNumber")
    project_name = config_data.get("ProjectName", "Unknown")
    
    mode = input("Retrieve(GET) / Send(PUSH) (G/P): ").strip().upper()
    if mode == "P":
        zip_path = os.path.join(current_dir, "sync.zip")
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
                for root, _, files in os.walk(current_dir):
                    for file in files:
                        if file.endswith(".zip") or file == CONFIG_FILENAME: continue
                        f_p = os.path.join(root, file)
                        z.write(f_p, os.path.relpath(f_p, current_dir))
            
            with open(zip_path, 'rb') as f:
                res = requests.post(f"{api_server}?action=push", data={"login_id": login_id, "login_pw": login_pw, "management_number": mgmt_num}, files={"file": f}, headers=HEADERS, timeout=30)
            if res.status_code == 200: print("Upload complete.")
            else: print(f"Failed: {res.status_code}")
        finally:
            if os.path.exists(zip_path): os.remove(zip_path)
            
    elif mode == "G":
        auth_params = {"login_id": login_id, "login_pw": login_pw} if is_secure_mgmt(mgmt_num) else {}
        res = requests.get(api_server, params={"action": "versions", "management_number": mgmt_num, **auth_params}, headers=HEADERS)
        if res.status_code == 200:
            versions = res.json().get("versions", [])
            print(f"Available Versions: {versions}")
            target = input("Select Version (Press Enter for latest): ").strip()
            r = requests.get(api_server, params={"action": "download", "management_number": mgmt_num, "version": target, **auth_params}, headers=HEADERS)
            if r.status_code == 200:
                with open("temp.zip", "wb") as f: f.write(r.content)
                with zipfile.ZipFile("temp.zip", "r") as z: z.extractall(current_dir)
                os.remove("temp.zip")
                print("Download complete.")

def pms_edit():
    print("--- PMS_Edit: Edit Project Configuration ---")
    current_dir = os.getcwd()
    config_path = os.path.join(current_dir, CONFIG_FILENAME)
    if not os.path.exists(config_path):
        print(f"Configuration file ({CONFIG_FILENAME}) not found.")
        return

    with open(config_path, "r", encoding="utf-8") as f:
        config_data = json.load(f)

    print(f"Current Project Name: {config_data.get('ProjectName')}")
    new_name = input("New Project Name (Leave blank to keep current): ").strip()
    if new_name:
        config_data['ProjectName'] = new_name

    print(f"Current Language: {config_data.get('Language')}")
    new_lang = input("New Language (Leave blank to keep current): ").strip()
    if new_lang:
        config_data['Language'] = new_lang

    print(f"Current ZipTarget: {config_data.get('ZipTarget')}")
    new_zip = input("New ZipTarget (e.g. src, Leave blank to keep current): ").strip()
    if new_zip:
        config_data['ZipTarget'] = new_zip

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=4, ensure_ascii=False)
    print("Configuration updated successfully.")

def pms_zip():
    print("--- PMS_zip: Folder Compression Wizard ---")
    current_dir = os.getcwd()
    config_path = os.path.join(current_dir, CONFIG_FILENAME)
    
    zip_target = current_dir
    project_name = os.path.basename(current_dir)

    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
            project_name = config_data.get("ProjectName", project_name)
            target_sub = config_data.get("ZipTarget", "")
            if target_sub:
                zip_target = os.path.join(current_dir, target_sub)
            else:
                # ZipTarget未設定 → ダイアログで選択
                print("ZipTarget is not set in configuration. Please select the folder to compress.")
                zip_target = select_directory("Select the folder to compress")
                if not zip_target:
                    print("Cancelled.")
                    return
                project_name = os.path.basename(zip_target)
    else:
        print("Project configuration not found. Please manually select the folder to compress.")
        zip_target = select_directory("Select the folder to compress")
        if not zip_target:
            print("Cancelled.")
            return
        project_name = os.path.basename(zip_target)

    # ZipTargetが指定されているが存在しない場合 → ダイアログで再選択
    if not os.path.exists(zip_target):
        print(f"Warning: Configured target directory does not exist: {zip_target}")
        print("Please manually select the folder to compress.")
        zip_target = select_directory("Select the folder to compress")
        if not zip_target:
            print("Cancelled.")
            return
        project_name = os.path.basename(zip_target)

    if not os.path.exists(zip_target):
        print("Error: Selected directory does not exist.")
        return

    print("Please select the save destination...")
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    out_zip = filedialog.asksaveasfilename(
        title="Select where to save the ZIP file",
        initialfile=f"{project_name}_export.zip",
        defaultextension=".zip",
        filetypes=[("ZIP Archive", "*.zip")]
    )
    root.destroy()
    
    if not out_zip:
        print("Save cancelled.")
        return
    
    print(f"Target directory: {zip_target}")
    print("Compressing...")
    try:
        with zipfile.ZipFile(out_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root_dir, dirs, files in os.walk(zip_target):
                for file in files:
                    file_p = os.path.join(root_dir, file)
                    if os.path.abspath(file_p) == os.path.abspath(out_zip):
                        continue
                    arcname = os.path.relpath(file_p, zip_target)
                    zipf.write(file_p, arcname)
        print(f"Compression completed! Output path: {out_zip}")
    except Exception as e:
        print(f"An error occurred during compression: {e}")

def pms_pkg():
    print("--- PMS_pkg: Project Build & Packaging ---")
    current_dir = os.getcwd()
    config_path = os.path.join(current_dir, CONFIG_FILENAME)
    if not os.path.exists(config_path):
        print("Configuration file not found. Please run PMS_Start first.")
        return

    with open(config_path, "r", encoding="utf-8") as f:
        config_data = json.load(f)
        
    do_compile = config_data.get("CompileOnPkg", False)
    language = config_data.get("Language", "").lower()
    
    if do_compile:
        print(f"Executing compilation (Language: {language})")
        if language in ["python", "py"]:
            print("Building Python script with PyInstaller...")
            main_script = input("Main script filename (e.g. main.py): ").strip()
            if main_script and os.path.exists(main_script):
                subprocess.run([sys.executable, "-m", "PyInstaller", "--onefile", main_script])
                print("Build completed.")
            else:
                print("Script not found. Skipping build.")
        elif language in ["dotnet", "c#"]:
            print("Executing dotnet build...")
            subprocess.run(["dotnet", "build", "-c", "Release"])
            print("Build completed.")
        elif language in ["rust", "rs", "cargo"]:
            print("Executing cargo build...")
            subprocess.run(["cargo", "build", "--release"])
            print("Build completed.")
        else:
            print("Automatic compilation for this language is not supported.")
            
    print("Proceeding to packaging (Zip creation)...")
    pms_zip()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower().replace("-", "_")
        if cmd == "pms_start": pms_start()
        elif cmd == "pms_edit": pms_edit()
        elif cmd == "pms_gui":
            try:
                import pms_gui
                pms_gui.run_gui()
            except ImportError as e:
                print(f"Failed to load GUI module: {e}")
        elif cmd == "pms_pkg": pms_pkg()
        elif cmd == "pms_zip": pms_zip()
        elif cmd == "pms_syns_setup": pms_syns_setup()
        elif cmd == "pms_syns_edit": pms_syns_edit()
        elif cmd == "pms_syns_join": pms_syns_join()
        elif cmd == "pms_syns": pms_syns()
        else: show_help()
    else:
        show_help()
