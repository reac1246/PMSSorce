$binPath = "c:\Users\Admin\ProjectManegements\bin"

# 管理者権限チェック
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "このスクリプトは管理者権限で実行する必要があります。PowerShellを管理者として実行してください。"
    exit
}

# インストールディレクトリの存在確認
if (-not (Test-Path $binPath)) {
    Write-Error "ディレクトリ $binPath が見つかりません。先にソース一式を配置してください。"
    exit
}

# 環境変数 PATH (Machine) を取得
$target = [EnvironmentVariableTarget]::Machine
$oldPath = [Environment]::GetEnvironmentVariable("Path", $target)

# 重複チェックをして追加
if ($oldPath -split ';' -notcontains $binPath) {
    $newPath = $oldPath + ";" + $binPath
    [Environment]::SetEnvironmentVariable("Path", $newPath, $target)
    Write-Host "システム環境変数 PATH に '$binPath' を追加しました。" -ForegroundColor Green
} else {
    Write-Host "PATH は既に設定されています。" -ForegroundColor Cyan
}

Write-Host "`nComplete! PMS command is now available." -ForegroundColor Yellow
Write-Host "設定を反映させるために、新しいコマンドプロンプトやPowerShellを開き直してください。"
