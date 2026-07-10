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
import glob

CONFIG_FILENAME = "infomation.psfl"

# Common Headers to avoid 404/Block from some hostings
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def is_secure_mgmt(mgmt_num):
    return mgmt_num.endswith('_Secure')

def get_global_config():
    path = r"C:\PMS\System\pms_global.json"
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def get_pms_version():
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    ver_path = os.path.join(base_path, "version.txt")
    if not os.path.exists(ver_path):
        ver_path = r"C:\PMS\System\version.txt"
    if os.path.exists(ver_path):
        try:
            with open(ver_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except:
            pass
    return "Unknown"

def select_api_server():
    global_cfg = get_global_config()
    g_api = global_cfg.get("ApiServer", "")
    if g_api: return g_api

    print("\nAPIサーバーのURLを入力してください / Enter API Server URL:")
    print("Example: https://your-server.com/PMS/api.php")
    url = input("URL: ").strip()
    if url and not url.startswith("http"):
        url = "https://" + url
    return url

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def select_directory(title="ディレクトリを選択してください"):
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    path = filedialog.askdirectory(title=title)
    root.destroy()
    return path

def select_multiple_items(title="複数選択してください"):
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    paths = filedialog.askopenfilenames(title=title)
    root.destroy()
    return list(paths)

def show_help():
    print("="*40)
    print("PMS - プロジェクト管理システム")
    print("="*40)
    print("利用可能なコマンド:")
    print("  PMS_Start      : プロジェクト設定の新規作成")
    print("  PMS_Edit       : プロジェクト設定の編集")
    print("  PMS_gui        : GUI設定画面を起動")
    print("  PMS_pkg        : プロジェクトのビルドとパッケージ化 (ZIP)")
    print("  PMS_zip        : フォルダ圧縮ウィザード")
    print("  PMS_syns_setup : 同期サーバーへの初回アップロードと設定")
    print("  PMS_syns_join  : 既存の同期プロジェクトへ参加 (ダウンロード)")
    print("  PMS_syns       : APIサーバーとの同期 (Push/Pull)")
    print("  PMS_syns_edit  : 管理番号と設定の変更")
    print("  PMS_Update     : 本ツールのアップデート確認と更新")
    print("="*40)

def pms_start():
    print("--- PMS_Start: プロジェクト作成ウィザード ---")
    project_name = input("プロジェクト名を入力してください: ").strip()
    language = input("メインの言語を入力してください (例: Python, Dotnet): ").strip()
    
    well_known_languages = ["python", "py", "dotnet", "c#", "cpp", "java", "rust", "rs", "cargo"]
    can_compile_auto = language.lower() in well_known_languages
    
    do_compile_pkg = "N"
    is_single_file = False
    if can_compile_auto:
        do_compile_pkg = input(f"PMS_pkg 実行時に自動コンパイルを行いますか？ (Y/N): ").strip().upper()
        if do_compile_pkg == "Y":
            single = input("単一ファイル(OneFile/SingleFile)としてビルドしますか？ (Y/N): ").strip().upper()
            is_single_file = (single == "Y")
    
    zip_target = input("圧縮対象ディレクトリ (未入力の場合は src となります): ").strip()
    if not zip_target:
        zip_target = "src"

    dev_dir = select_directory("プロジェクトのルートディレクトリを選択してください")

    if not dev_dir:
        print("エラー: ディレクトリが選択されませんでした。")
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
    
    print("\n設定完了！保存しました。")

def pms_syns_setup():
    print("--- PMS_syns_setup: 同期API設定 ---")
    current_dir = os.getcwd()
    config_path = os.path.join(current_dir, CONFIG_FILENAME)
    config_data = {}
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
    else:
        print("エラー: 設定ファイルが見つかりません。先に PMS_Start を実行してください。")
        return

    api_server = select_api_server()
    if not api_server: return

    login_id = input("\nログインID: ").strip()
    login_pw = input("パスワード: ").strip()
    
    print("認証情報を確認しています...")
    try:
        res = requests.post(f"{api_server}?action=verify", json={"login_id": login_id, "login_pw": login_pw}, headers=HEADERS, timeout=5)
        if res.status_code == 200:
            print("アカウント認証成功。続行します。")
        else:
            print(f"エラーコード: {res.status_code} - {res.text}")
            return
    except Exception as e:
        print(f"エラー: サーバーに接続できません。{e}")
        return

    print("PMS管理番号 (PMS ID) を入力してください")
    mgmt_prompt = "'PMS_' から始まる既存のIDを入力、または新規IDのサフィックスを入力 (空白で自動生成): "
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
        
        print("データサーバーへアップロード中...")
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
            print(f"セットアップ完了。管理番号: {mgmt_num}")
        else:
            print(f"セットアップ失敗: {upload_res.status_code} - {upload_res.text}")
            return
    except Exception as e:
        print(f"エラー: {e}")
        return
    finally:
        if os.path.exists(zip_path): os.remove(zip_path)

    config_data.update({"ApiServer": api_server, "LoginID": login_id, "LoginPW": login_pw, "ManagementNumber": mgmt_num})
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=4, ensure_ascii=False)

def pms_syns_edit():
    print("--- PMS_syns_edit: 管理番号と設定の変更 ---")
    current_dir = os.getcwd()
    config_path = os.path.join(current_dir, CONFIG_FILENAME)
    if not os.path.exists(config_path):
        print("設定ファイルが見つかりません。")
        return
        
    with open(config_path, "r", encoding="utf-8") as f:
        config_data = json.load(f)
        
    api_server = config_data.get("ApiServer")
    login_id = config_data.get("LoginID")
    login_pw = config_data.get("LoginPW")
    old_mgmt = config_data.get("ManagementNumber")
    
    print(f"現在の管理番号: {old_mgmt}")
    new_mgmt = input("新しい管理番号を入力してください: ").strip()
    if not new_mgmt or new_mgmt == old_mgmt:
        print("変更されませんでした。")
        return
        
    change_key = ""
    old_parts = old_mgmt.split('_')
    new_parts = new_mgmt.split('_')
    if len(old_parts) > 1 and len(new_parts) > 1 and old_parts[1] != new_parts[1]:
        print("警告: ユーザーID部分の変更を検出しました。")
        change_key = input("admin.php で発行された ChangeKey を入力してください: ").strip()
        if not change_key:
            print("ChangeKey は必須です。")
            return

    print("サーバーへ変更を適用しています...")
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
            print(f"管理番号を {new_mgmt} に更新しました。")
        else:
            print(f"更新失敗: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"エラー: {e}")

def pms_syns_join():
    print("--- PMS_syns_join: プロジェクトに参加 ---")
    api_server = select_api_server()
    if not api_server: return

    login_id = input("ログインIDを入力してください: ").strip()
    login_pw = input("パスワードを入力してください: ").strip()
    mgmt_num = input("参加する PMS管理番号 を入力してください: ").strip()
    
    auth_params = {"login_id": login_id, "login_pw": login_pw}
    try:
        res = requests.get(f"{api_server}", params={"action": "info", "management_number": mgmt_num, **auth_params}, headers=HEADERS, timeout=5)
        if res.status_code != 200:
            print("プロジェクト情報が見つかりません。")
            return
        info = res.json()
        print(f"プロジェクト: {info.get('project_name')} (バージョン: {info.get('latest_version')})")
    except Exception as e:
        print(f"エラー: {e}"); return

    dev_dir = select_directory("保存先ディレクトリを選択してください")
    if not dev_dir: return

    print("ダウンロード中...")
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
            print("展開が完了しました。")
    except Exception as e:
        print(f"エラー: {e}")

def pms_syns():
    print("--- PMS_syns: APIサーバーと同期 ---")
    current_dir = os.getcwd()
    config_path = os.path.join(current_dir, CONFIG_FILENAME)
    if not os.path.exists(config_path):
        print("エラー: 設定ファイルが見つかりません。先に PMS_syns_setup または PMS_Start を実行してください。")
        return
        
    with open(config_path, "r", encoding="utf-8") as f:
        config_data = json.load(f)
        
    api_server = config_data.get("ApiServer")
    login_id = config_data.get("LoginID")
    login_pw = config_data.get("LoginPW")
    mgmt_num = config_data.get("ManagementNumber")
    project_name = config_data.get("ProjectName", "Unknown")
    
    if not api_server or not login_id or not mgmt_num:
        print("エラー: サーバー設定が不完全です。PMS_syns_setup を実行してください。")
        return
        
    mode = input("取得(GET) / 送信(PUSH) を選択してください (G/P): ").strip().upper()
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
            if res.status_code == 200: print("アップロード完了。")
            else: print(f"失敗しました: {res.status_code}")
        finally:
            if os.path.exists(zip_path): os.remove(zip_path)
            
    elif mode == "G":
        auth_params = {"login_id": login_id, "login_pw": login_pw} if is_secure_mgmt(mgmt_num) else {}
        res = requests.get(api_server, params={"action": "versions", "management_number": mgmt_num, **auth_params}, headers=HEADERS)
        if res.status_code == 200:
            versions = res.json().get("versions", [])
            print(f"利用可能なバージョン: {versions}")
            target = input("取得するバージョンを選択してください (Enterで最新): ").strip()
            r = requests.get(api_server, params={"action": "download", "management_number": mgmt_num, "version": target, **auth_params}, headers=HEADERS)
            if r.status_code == 200:
                with open("temp.zip", "wb") as f: f.write(r.content)
                with zipfile.ZipFile("temp.zip", "r") as z: z.extractall(current_dir)
                os.remove("temp.zip")
                print("ダウンロード完了。")

def pms_edit():
    print("--- PMS_Edit: プロジェクト設定の編集 ---")
    current_dir = os.getcwd()
    config_path = os.path.join(current_dir, CONFIG_FILENAME)
    if not os.path.exists(config_path):
        print(f"設定ファイル ({CONFIG_FILENAME}) が見つかりません。")
        return

    with open(config_path, "r", encoding="utf-8") as f:
        config_data = json.load(f)

    print(f"現在のプロジェクト名: {config_data.get('ProjectName')}")
    new_name = input("新しいプロジェクト名 (空白で変更なし): ").strip()
    if new_name:
        config_data['ProjectName'] = new_name

    print(f"現在の言語: {config_data.get('Language')}")
    new_lang = input("新しい言語 (空白で変更なし): ").strip()
    if new_lang:
        config_data['Language'] = new_lang

    print(f"現在の圧縮対象(ZipTarget): {config_data.get('ZipTarget')}")
    new_zip = input("新しい圧縮対象 (例: src, bin/Release など。空白で変更なし): ").strip()
    if new_zip:
        config_data['ZipTarget'] = new_zip

    print(f"現在の単一ファイルビルド(IsSingleFile)設定: {config_data.get('IsSingleFile', False)}")
    new_single = input("単一ファイルとしてビルドしますか？ (Y/N, 空白で変更なし): ").strip().upper()
    if new_single in ["Y", "N"]:
        config_data['IsSingleFile'] = (new_single == "Y")

    global_cfg = get_global_config()
    print(f"現在のAPIサーバー(SV): {global_cfg.get('ApiServer', '')}")
    new_api = input("新しいAPIサーバーURL (空白で変更なし): ").strip()
    if new_api:
        if not new_api.startswith("http"):
            new_api = "https://" + new_api
        global_cfg['ApiServer'] = new_api
        config_data['ApiServer'] = new_api
        
        g_path = r"C:\PMS\System\pms_global.json"
        os.makedirs(os.path.dirname(g_path), exist_ok=True)
        with open(g_path, "w", encoding="utf-8") as gf:
            json.dump(global_cfg, gf, indent=4, ensure_ascii=False)

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=4, ensure_ascii=False)
    print("設定が正常に更新されました。")

def pms_zip(zip_target_override=None):
    print("--- PMS_zip: フォルダ圧縮ウィザード ---")
    current_dir = os.getcwd()
    config_path = os.path.join(current_dir, CONFIG_FILENAME)
    
    zip_target = current_dir
    project_name = os.path.basename(current_dir)

    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
            project_name = config_data.get("ProjectName", project_name)
            
            target_sub = zip_target_override if zip_target_override else config_data.get("ZipTarget", "")
            
            if target_sub:
                zip_target = os.path.join(current_dir, target_sub)
            else:
                print("設定ファイルに ZipTarget が指定されていません。圧縮するフォルダを選択してください。")
                zip_target = select_directory("圧縮するフォルダを選択")
                if not zip_target:
                    print("キャンセルされました。")
                    return
                project_name = os.path.basename(zip_target)
    else:
        print("設定ファイルが見つかりません。圧縮するフォルダを手動で選択してください。")
        zip_target = select_directory("圧縮するフォルダを選択")
        if not zip_target:
            print("キャンセルされました。")
            return
        project_name = os.path.basename(zip_target)

    if not os.path.exists(zip_target):
        print(f"警告: 指定されたディレクトリが存在しません: {zip_target}")
        print("圧縮するフォルダを手動で選択してください。")
        zip_target = select_directory("圧縮するフォルダを選択")
        if not zip_target:
            print("キャンセルされました。")
            return
        project_name = os.path.basename(zip_target)

    print("保存先を選択してください...")
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    out_zip = filedialog.asksaveasfilename(
        title="ZIPファイルの保存先を選択",
        initialfile=f"{project_name}_export.zip",
        defaultextension=".zip",
        filetypes=[("ZIP Archive", "*.zip")]
    )
    root.destroy()
    
    if not out_zip:
        print("保存がキャンセルされました。")
        return
    
    print(f"圧縮対象: {zip_target}")
    print("圧縮中...")
    try:
        with zipfile.ZipFile(out_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root_dir, dirs, files in os.walk(zip_target):
                for file in files:
                    file_p = os.path.join(root_dir, file)
                    if os.path.abspath(file_p) == os.path.abspath(out_zip):
                        continue
                    arcname = os.path.relpath(file_p, zip_target)
                    zipf.write(file_p, arcname)
        print(f"圧縮完了！出力先: {out_zip}")
    except Exception as e:
        print(f"圧縮中にエラーが発生しました: {e}")

def get_dotnet_publish_dir(base_dir):
    search_path = os.path.join(base_dir, 'bin', 'Release', '*', 'publish')
    found = glob.glob(search_path)
    if found:
        return os.path.relpath(found[0], base_dir)
    return None

def pms_pkg():
    print("--- PMS_pkg: プロジェクトビルド & パッケージ化 ---")
    current_dir = os.getcwd()
    config_path = os.path.join(current_dir, CONFIG_FILENAME)
    if not os.path.exists(config_path):
        print("エラー: 設定ファイルが見つかりません。先に PMS_Start を実行してください。")
        return

    with open(config_path, "r", encoding="utf-8") as f:
        config_data = json.load(f)
        
    do_compile = config_data.get("CompileOnPkg", False)
    is_single_file = config_data.get("IsSingleFile", True)
    language = config_data.get("Language", "").lower()
    
    new_zip_target = None
    
    if do_compile:
        print(f"コンパイル処理を実行します (言語: {language}, 単一ファイル化: {is_single_file})")
        if language in ["python", "py"]:
            print("PyInstaller を使用してビルドします...")
            main_script = input("メインスクリプトのファイル名 (例: main.py): ").strip()
            if main_script and os.path.exists(main_script):
                cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm"]
                if is_single_file:
                    cmd.append("--onefile")
                else:
                    cmd.append("--onedir")
                cmd.append(main_script)
                subprocess.run(cmd)
                print("ビルド完了。出力ディレクトリを 'dist' に設定します。")
                new_zip_target = "dist"
            else:
                print("スクリプトが見つからないため、ビルドをスキップします。")
                
        elif language in ["dotnet", "c#"]:
            if is_single_file:
                print("dotnet publish を実行しています...")
                cmd = ["dotnet", "publish", "-c", "Release", "-p:PublishSingleFile=true"]
                subprocess.run(cmd)
                print("ビルド完了。publish ディレクトリを探しています...")
                pub_dir = get_dotnet_publish_dir(current_dir)
                if pub_dir:
                    print(f"publish ディレクトリを発見しました: {pub_dir}")
                    new_zip_target = pub_dir
                else:
                    print("警告: publish ディレクトリが見つかりませんでした。")
            else:
                print("dotnet build を実行しています...")
                cmd = ["dotnet", "build", "-c", "Release"]
                subprocess.run(cmd)
                print("ビルド完了。bin/Release を探しています...")
                # 通常ビルド時は bin/Release/netX.X のようなディレクトリを探す
                search_path = os.path.join(current_dir, 'bin', 'Release', '*')
                found = [p for p in glob.glob(search_path) if os.path.isdir(p)]
                if found:
                    new_zip_target = os.path.relpath(found[0], current_dir)
                    print(f"出力ディレクトリを発見しました: {new_zip_target}")
                else:
                    new_zip_target = os.path.join("bin", "Release")
                    print(f"出力ディレクトリを設定: {new_zip_target}")
                
        elif language in ["rust", "rs", "cargo"]:
            print("cargo build を実行しています...")
            subprocess.run(["cargo", "build", "--release"])
            print("ビルド完了。")
            new_zip_target = os.path.join("target", "release")
            
        else:
            print("この言語の自動コンパイルはサポートされていません。")
            
    if new_zip_target:
        update_cfg = input(f"設定ファイル内の ZipTarget を自動的に '{new_zip_target}' に更新して保存しますか？ (Y/N): ").strip().upper()
        if update_cfg == "Y":
            config_data["ZipTarget"] = new_zip_target
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            print("ZipTarget を更新しました。")

    print("パッケージ化 (Zip作成) に進みます...")
    pms_zip(zip_target_override=new_zip_target)

def pms_update(api_url=None):
    print("--- PMS_Update: アップデートの確認 ---")
    current_version = get_pms_version()
    print(f"現在のバージョン: {current_version}")
    
    global_cfg = get_global_config()
    api_server = api_url if api_url else global_cfg.get("ApiServer", "")
    
    if not api_server:
        print("APIサーバーが設定されていません。PMS_Setup を実行して設定してください。")
        return

    if api_server and not api_server.startswith("http"):
        api_server = "https://" + api_server

    if api_url:
        lang = global_cfg.get("Language", "日本語")
        if "日本" in lang:
            msg = f"今後このSV ({api_server}) を利用するように再登録しますか？ (Y/N): "
        else:
            msg = f"Do you want to re-register and use this SV ({api_server}) from now on? (Y/N): "
        
        ans = input(msg).strip().upper()
        if ans == "Y":
            global_cfg["ApiServer"] = api_server
            g_path = r"C:\PMS\System\pms_global.json"
            os.makedirs(os.path.dirname(g_path), exist_ok=True)
            with open(g_path, "w", encoding="utf-8") as gf:
                json.dump(global_cfg, gf, indent=4, ensure_ascii=False)
            print("再登録しました。" if "日本" in lang else "Re-registered.")

    print(f"サーバーに問い合わせ中... ({api_server})")
    try:
        res = requests.get(api_server, params={"action": "check_update", "current_version": current_version}, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            try:
                data = res.json()
            except ValueError:
                print("サーバーからの応答が正しいJSONではありません。")
                return
            has_update = data.get("has_update", False)
            latest_ver = data.get("latest_version", "")
            dl_url = data.get("download_url", "")
            
            if has_update and dl_url:
                print(f"新しいバージョン {latest_ver} が見つかりました！")
                ans = input("アップデートをダウンロードしてインストールしますか？ (Y/N): ").strip().upper()
                if ans == "Y":
                    print("ダウンロード中...")
                    dl_res = requests.get(dl_url, stream=True, headers=HEADERS)
                    if dl_res.status_code == 200:
                        installer_path = os.path.join(os.getcwd(), "PMS_Setup_New.exe")
                        with open(installer_path, "wb") as f:
                            shutil.copyfileobj(dl_res.raw, f)
                        print(f"ダウンロード完了。インストーラーを起動します: {installer_path}")
                        os.startfile(installer_path)
                        sys.exit(0)
                    else:
                        print("ダウンロードに失敗しました。")
            else:
                print("現在、最新バージョンを使用しています。")
        else:
            print(f"サーバーがアップデートAPIをサポートしていないか、エラーが発生しました: {res.status_code}")
    except Exception as e:
        print(f"アップデートの確認中にエラーが発生しました: {e}")

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
                print(f"GUIモジュールの読み込みに失敗しました: {e}")
        elif cmd == "pms_pkg": pms_pkg()
        elif cmd == "pms_zip": pms_zip()
        elif cmd == "pms_syns_setup": pms_syns_setup()
        elif cmd == "pms_syns_edit": pms_syns_edit()
        elif cmd == "pms_syns_join": pms_syns_join()
        elif cmd == "pms_syns": pms_syns()
        elif cmd == "pms_update":
            update_url = None
            for arg in sys.argv[2:]:
                if arg.upper().startswith("--URL:"):
                    update_url = arg[6:]
                    break
            pms_update(api_url=update_url)
        else: show_help()
    else:
        show_help()
