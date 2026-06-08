param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Target
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$targetName = ($Target -join ' ').Trim()
if ($targetName -ne 'Work On') {
    Write-Host 'Usage: git update Work On'
    exit 1
}

$repoRoot = 'D:\system_folder\Desktop\Work On'
Set-Location $repoRoot

$changes = git status --porcelain
if (-not $changes) {
    Write-Host 'No changes to update.'
    exit 0
}

$branch = git branch --show-current
if (-not $branch) {
    Write-Host 'Cannot determine the current Git branch.'
    exit 1
}

$timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm'
git add -A
git commit -m "Update Work On: $timestamp"
git push origin $branch
