# 📁 PMS — Project Management System

**PMS** は、開発プロジェクトのパッケージング・同期・インストールをターミナルから一発で行える、軽量な CLI ツールです。  
Python で動き、Windows 環境に最適化されています。

---

## ✨ 主な機能

| コマンド | 説明 |
|---|---|
| `PMS_Start` | プロジェクト設定ファイル（`infomation.psfl`）を対話形式で作成 |
| `PMS_Edit` | 既存設定ファイルを編集 |
| `PMS_gui` | Tkinter ベースのグラフィカル設定 UI を起動 |
| `PMS_pkg` | プロジェクトをビルド & Zip パッケージ化 |
| `PMS_zip` | フォルダ圧縮ウィザード |
| `PMS_syns_setup` | API サーバーへ初回アップロード & 同期設定 |
| `PMS_syns_join` | 既存同期プロジェクトに参加（ダウンロード） |
| `PMS_syns` | API サーバーと Push / Pull 同期 |
| `PMS_syns_edit` | 管理番号・同期設定の変更 |

---

## 📦 インストール方法

### 方法 1：配布 EXE を使用（推奨）

`PMS_Setup.exe` を **管理者として実行** するだけです。  
`C:\PMS\System\bin` に自動でインストールされ、PATH も設定されます。

### 方法 2：ソースから手動セットアップ

```powershell
# 1. リポジトリをクローン
git clone https://github.com/<your-username>/PMSSorce.git
cd PMSSorce

# 2. 依存ライブラリをインストール
pip install -r requirements.txt

# 3. PATH を通す（管理者 PowerShell で実行）
.\install.ps1
```

---

## 🔨 EXE ビルド方法

```powershell
# プロジェクトルートで実行
python build_exes.py
```

ビルドが完了すると `dist/PMS_Setup.exe` が生成されます。

**ビルドの流れ：**
1. `PMS.exe`（コアCLI）をビルド
2. `PMS_Setup.exe`（インストーラー）を PMS.exe と bat/src ファイルを同梱してビルド

---

## 📋 必要環境

- **OS**: Windows 10 / 11
- **Python**: 3.10 以上（ビルド時）
- **ライブラリ**: `requirements.txt` 参照

```
flask
requests
pyzipper
pyinstaller
```

---

## 🗂 プロジェクト構成

```
PMSSorce/
├── src/
│   ├── pms_core.py          # CLI メインロジック
│   ├── pms_gui.py           # Tkinter GUI
│   ├── pms_installer_logic.py  # インストーラー UI
│   └── pms_server.py        # Flask API サーバー（セルフホスト用）
├── bin/
│   ├── PMS.bat              # PMS CLI ランチャー
│   ├── PMS_Start.bat
│   ├── PMS_Edit.bat
│   └── ...（各コマンドの .bat ファイル）
├── build_exes.py            # ビルドスクリプト
├── requirements.txt
├── install.ps1              # PATH 設定スクリプト（管理者用）
├── install_deps.bat         # 依存インストールバッチ
└── pms_icon.ico
```

---

## 🌐 同期サーバーについて

PMS には **ファイル同期 API サーバー**（`pms_server.py`）が付属しています。  
自前のサーバーにデプロイすることで、チーム間でプロジェクトファイルを共有できます。

```powershell
# サーバー起動（デフォルト: ポート 5000）
python src/pms_server.py

# ポートを指定する場合
python src/pms_server.py 8080
```

API エンドポイント:
- `POST /verify` — 認証確認
- `POST /setup` — 初回プロジェクト登録
- `POST /push` — バージョンアップ
- `GET /info` — プロジェクト情報取得
- `GET /versions` — バージョン一覧
- `GET /download` — バージョン指定ダウンロード

---

## 🏷 設定ファイル（`infomation.psfl`）

`PMS_Start` または `PMS_gui` で生成される JSON ファイル。

```json
{
    "ProjectName": "MyApp",
    "Language": "Python",
    "CompileOnPkg": true,
    "ZipTarget": "src",
    "DevelopmentDir": "C:/path/to/project",
    "ApiServer": "https://your-server/api.php",
    "LoginID": "your_id",
    "LoginPW": "your_pw",
    "ManagementNumber": "PMS_your_id_myapp"
}
```

> ⚠️ `infomation.psfl` には認証情報が含まれるため、`.gitignore` で除外されています。**Git にコミットしないでください。**

---

## 📄 ライセンス

MIT License — 詳しくは [LICENSE](LICENSE) ファイルを参照してください。
