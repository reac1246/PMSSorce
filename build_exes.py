import subprocess
import os
import sys

def build_package():
    print("=== PMS Full Build Process ===")
    
    # 必要ライブラリのインストール
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    # ビルドに使う Python インタープリタ (このスクリプトを実行した Python を使う)
    python = sys.executable

    # 出力先ディレクトリの準備
    os.makedirs("dist", exist_ok=True)

    # -----------------------------------------------
    # 1. Build core program (console, onefile)
    # -----------------------------------------------
    print("\n[1/2] Building PMS.exe...")
    core_cmd = [
        python, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--console",
        "--icon", "pms_icon.ico",
        "--name", "PMS",
        "--add-data", f"version.txt{os.pathsep}.",
        # src/ 配下のモジュールを解決するためのパス
        "--paths", os.path.join(os.path.dirname(__file__), "src"),
        "--hidden-import", "pyzipper",
        "--hidden-import", "requests",
        # pms_gui は src/ にあるので完全にパスを通して収録する
        "--hidden-import", "pms_gui",
        "--hidden-import", "pms_server",
        "--collect-submodules", "tkinter",
        "--clean",
        os.path.join("src", "pms_core.py")
    ]
    subprocess.run(core_cmd, check=True)

    # -----------------------------------------------
    # 2. Build installer (windowed, onefile, uac-admin)
    # -----------------------------------------------
    print("\n[2/2] Building PMS_Setup.exe...")

    # PMS.exe が存在するか確認
    pms_exe = os.path.join("dist", "PMS.exe")
    if not os.path.exists(pms_exe):
        raise FileNotFoundError(
            f"dist/PMS.exe が見つかりません。Step 1 のビルドが失敗している可能性があります: {pms_exe}"
        )

    # bin/ のファイルを個別に --add-data で指定（ワイルドカードは不安定なので展開する）
    add_data_args = []

    # PMS.exe を bin/ として同梱
    add_data_args += ["--add-data", f"{pms_exe}{os.pathsep}bin"]

    # bin/ 内の各 .bat ファイルを個別に追加
    bin_dir = "bin"
    if os.path.isdir(bin_dir):
        for fname in os.listdir(bin_dir):
            fpath = os.path.join(bin_dir, fname)
            if os.path.isfile(fpath):
                add_data_args += ["--add-data", f"{fpath}{os.pathsep}bin"]

    # src/ 内の各 .py ファイルを個別に追加
    src_dir = "src"
    if os.path.isdir(src_dir):
        for fname in os.listdir(src_dir):
            fpath = os.path.join(src_dir, fname)
            if os.path.isfile(fpath) and not fname.startswith("__"):
                add_data_args += ["--add-data", f"{fpath}{os.pathsep}src"]

    # version.txt を追加
    if os.path.isfile("version.txt"):
        add_data_args += ["--add-data", f"version.txt{os.pathsep}."]


    installer_cmd = [
        python, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--uac-admin",
        "--icon", "pms_icon.ico",
        "--name", "PMS_Setup",
        "--clean",
    ] + add_data_args + [
        os.path.join("src", "pms_installer_logic.py")
    ]
    subprocess.run(installer_cmd, check=True)

    print("\n" + "="*30)
    print("BUILD COMPLETE!")
    print("配布物: dist/PMS_Setup.exe")
    print("="*30)

if __name__ == "__main__":
    try:
        build_package()
    except Exception as e:
        print(f"\nBUILD FAILED: {e}")
        with open("BuildError.log", "w", encoding="utf-8") as f:
            f.write(str(e))
        sys.exit(1)
