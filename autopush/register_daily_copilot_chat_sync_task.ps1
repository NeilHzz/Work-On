param(
    [Parameter(Mandatory = $true)]
    [string]$CloudRoot,

    [Parameter(Mandatory = $false)]
    [string]$WorkspacePath = (Get-Location).Path,

    [Parameter(Mandatory = $false)]
    [string]$WorkspaceName,

    [Parameter(Mandatory = $false)]
    [string]$TaskName,

    [Parameter(Mandatory = $false)]
    [ValidatePattern('^([01]\d|2[0-3]):[0-5]\d$')]
    [string]$DailyTime = '00:05',

    [Parameter(Mandatory = $false)]
    [switch]$PreviewOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptPath = Join-Path $PSScriptRoot 'sync_copilot_chat_to_cloud.ps1'
if (-not (Test-Path -LiteralPath $scriptPath)) {
    throw "sync_copilot_chat_to_cloud.ps1 was not found next to this script."
}

$resolvedWorkspacePath = (Resolve-Path -LiteralPath $WorkspacePath).Path
$resolvedCloudRoot = [System.IO.Path]::GetFullPath($CloudRoot)
$effectiveWorkspaceName = if ($WorkspaceName) {
    $WorkspaceName
}
else {
    (Split-Path -Leaf $resolvedWorkspacePath) -replace '[^A-Za-z0-9._-]+', '_'
}

$effectiveTaskName = if ($TaskName) {
    $TaskName
}
else {
    "CopilotChatDailySync-$effectiveWorkspaceName"
}

$arguments = @(
    '-NoProfile',
    '-ExecutionPolicy', 'Bypass',
    '-File', ('"{0}"' -f $scriptPath),
    '-CloudRoot', ('"{0}"' -f $resolvedCloudRoot),
    '-WorkspacePath', ('"{0}"' -f $resolvedWorkspacePath),
    '-WorkspaceName', ('"{0}"' -f $effectiveWorkspaceName),
    '-Mode', 'auto'
) -join ' '

Write-Host "[task] task name: $effectiveTaskName"
Write-Host "[task] daily time: $DailyTime"
Write-Host "[task] workspace: $resolvedWorkspacePath"
Write-Host "[task] cloud root: $resolvedCloudRoot"
Write-Host "[task] command: powershell.exe $arguments"

if ($PreviewOnly) {
    Write-Host "[task] preview only; no scheduled task was created."
    return
}

$trigger = New-ScheduledTaskTrigger -Daily -At $DailyTime
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $arguments -WorkingDirectory $PSScriptRoot
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask -TaskName $effectiveTaskName -Trigger $trigger -Action $action -Settings $settings -Description 'Daily auto sync for VS Code Copilot Chat state.' -Force | Out-Null

Write-Host "[task] scheduled task registered successfully."