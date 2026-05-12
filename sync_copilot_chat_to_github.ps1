param(
    [Parameter(Mandatory = $true)]
    [string]$RepoPath,

    [Parameter(Mandatory = $false)]
    [string]$WorkspacePath = (Get-Location).Path,

    [Parameter(Mandatory = $false)]
    [string]$WorkspaceName,

    [Parameter(Mandatory = $false)]
    [ValidateSet("push", "pull", "auto")]
    [string]$Mode = "auto",

    [Parameter(Mandatory = $false)]
    [string]$CommitMessage,

    [Parameter(Mandatory = $false)]
    [switch]$SkipGitNetwork
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "[github-sync] $Message"
}

function Invoke-Git {
    param(
        [string]$Repository,
        [string[]]$Arguments,
        [switch]$IgnoreExitCode
    )

    $stdoutFile = [System.IO.Path]::GetTempFileName()
    $stderrFile = [System.IO.Path]::GetTempFileName()
    try {
        $argumentString = ($Arguments | ForEach-Object {
            if ($_ -match '[\s"]') {
                '"{0}"' -f (($_ -replace '"', '\"'))
            }
            else {
                $_
            }
        }) -join ' '

        $process = Start-Process -FilePath 'git.exe' -WorkingDirectory $Repository -ArgumentList $argumentString -NoNewWindow -Wait -PassThru -RedirectStandardOutput $stdoutFile -RedirectStandardError $stderrFile
        $output = if (Test-Path -LiteralPath $stdoutFile) {
            Get-Content -LiteralPath $stdoutFile -Raw
        }
        else {
            ''
        }
        $stderrText = if (Test-Path -LiteralPath $stderrFile) {
            Get-Content -LiteralPath $stderrFile -Raw
        }
        else {
            ''
        }
    }
    finally {
        if (Test-Path -LiteralPath $stdoutFile) {
            Remove-Item -LiteralPath $stdoutFile -Force -ErrorAction SilentlyContinue
        }
        if (Test-Path -LiteralPath $stderrFile) {
            Remove-Item -LiteralPath $stderrFile -Force -ErrorAction SilentlyContinue
        }
    }

    $exitCode = $process.ExitCode
    if (-not $IgnoreExitCode -and $exitCode -ne 0) {
        $joined = $Arguments -join ' '
        throw "git $joined failed with exit code $exitCode`n$output`n$stderrText"
    }

    if (-not [string]::IsNullOrWhiteSpace($stderrText)) {
        $stderrText.Trim().Split([Environment]::NewLine) | ForEach-Object {
            if (-not [string]::IsNullOrWhiteSpace($_)) {
                Write-Step "git warning: $_"
            }
        }
    }

    return [PSCustomObject]@{
        ExitCode = $exitCode
        Output = $output
    }
}

function Test-GitRemoteExists {
    param([string]$Repository)
    $result = Invoke-Git -Repository $Repository -Arguments @('remote') -IgnoreExitCode
    if ($result.ExitCode -ne 0) {
        return $false
    }

    return -not [string]::IsNullOrWhiteSpace($result.Output)
}

function Get-WorkspaceKey {
    param(
        [string]$WorkspaceResolvedPath,
        [string]$WorkspaceName
    )

    if ($WorkspaceName) {
        return $WorkspaceName
    }

    return (Split-Path -Leaf $WorkspaceResolvedPath) -replace '[^A-Za-z0-9._-]+', '_'
}

$repoResolved = (Resolve-Path -LiteralPath $RepoPath).Path
$workspaceResolved = (Resolve-Path -LiteralPath $WorkspacePath).Path
$workspaceKey = Get-WorkspaceKey -WorkspaceResolvedPath $workspaceResolved -WorkspaceName $WorkspaceName
$localSyncScript = Join-Path $PSScriptRoot 'sync_copilot_chat_to_cloud.ps1'

if (-not (Test-Path -LiteralPath (Join-Path $repoResolved '.git'))) {
    throw "RepoPath is not a git repository: $repoResolved"
}

if (-not (Test-Path -LiteralPath $localSyncScript)) {
    throw "sync_copilot_chat_to_cloud.ps1 was not found next to this script."
}

$hasRemote = Test-GitRemoteExists -Repository $repoResolved

Write-Step "repo: $repoResolved"
Write-Step "workspace: $workspaceResolved"
Write-Step "workspace key: $workspaceKey"
Write-Step "mode: $Mode"
Write-Step "has remote: $hasRemote"

if (($Mode -eq 'pull' -or $Mode -eq 'auto') -and $hasRemote -and -not $SkipGitNetwork) {
    Write-Step 'git pull --rebase --autostash'
    Invoke-Git -Repository $repoResolved -Arguments @('pull', '--rebase', '--autostash') | Out-Null
}
elseif (($Mode -eq 'pull' -or $Mode -eq 'auto') -and -not $hasRemote) {
    Write-Step 'skip network pull because no remote is configured'
}

Write-Step "export/import chat state via local sync script"
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $localSyncScript -CloudRoot $repoResolved -WorkspacePath $workspaceResolved -WorkspaceName $workspaceKey -Mode $Mode
if ($LASTEXITCODE -ne 0) {
    throw "Underlying local sync script failed with exit code $LASTEXITCODE"
}

if ($Mode -eq 'pull') {
    Write-Step 'pull mode finished; no git commit or push required'
    return
}

$syncFolderName = 'vscode-copilot-sync'
$syncFolderPath = Join-Path $repoResolved $syncFolderName

if (-not (Test-Path -LiteralPath $syncFolderPath)) {
    throw "Expected sync folder was not created: $syncFolderPath"
}

Invoke-Git -Repository $repoResolved -Arguments @('add', '--all', '--', $syncFolderName) | Out-Null
$status = Invoke-Git -Repository $repoResolved -Arguments @('status', '--porcelain', '--', $syncFolderName)

if ([string]::IsNullOrWhiteSpace($status.Output)) {
    Write-Step 'no staged changes under vscode-copilot-sync; nothing to commit'
    return
}

$effectiveCommitMessage = if ($CommitMessage) {
    $CommitMessage
}
else {
    "sync copilot chat state for $workspaceKey on $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
}

Write-Step "git commit: $effectiveCommitMessage"
Invoke-Git -Repository $repoResolved -Arguments @('commit', '-m', $effectiveCommitMessage) | Out-Null

if ($hasRemote -and -not $SkipGitNetwork) {
    Write-Step 'git push'
    Invoke-Git -Repository $repoResolved -Arguments @('push') | Out-Null
}
elseif (-not $hasRemote) {
    Write-Step 'skip git push because no remote is configured'
}
else {
    Write-Step 'skip git push because SkipGitNetwork was requested'
}

Write-Step 'GitHub sync completed.'