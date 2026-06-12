# sync_chat_logs.ps1
# 每天运行一次：导出聊天记录 → git commit + push
# 由 Windows 任务计划程序调用

$RepoRoot = "E:\Data\Desktop\Work On"
$PythonExe = "$RepoRoot\.venv\Scripts\python.exe"
$Script = "$RepoRoot\export_chat_logs.py"

# 1. 导出聊天记录
& $PythonExe $Script

# 2. 如果有变更，提交并推送
Set-Location $RepoRoot
$changed = git status --porcelain chat_logs/
if ($changed) {
    git add chat_logs/
    $date = Get-Date -Format "yyyy-MM-dd"
    git commit -m "Update chat logs: $date"
    git push origin main
    Write-Host "聊天记录已同步到 GitHub。"
} else {
    Write-Host "聊天记录无变更，跳过提交。"
}
