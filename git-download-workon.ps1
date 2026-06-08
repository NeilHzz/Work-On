param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Target
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$targetName = ($Target -join ' ').Trim()
if ($targetName -ne 'Work On') {
    Write-Host 'Usage: git download Work On'
    exit 1
}

$repoRoot = 'D:\system_folder\Desktop\Work On'
Set-Location $repoRoot

$branch = git branch --show-current
if (-not $branch) {
    Write-Host 'Cannot determine the current Git branch.'
    exit 1
}

git pull --rebase --autostash origin $branch
