param(
    [Parameter(Mandatory = $true)]
    [string]$CloudRoot,

    [Parameter(Mandatory = $false)]
    [string]$WorkspacePath = (Get-Location).Path,

    [Parameter(Mandatory = $false)]
    [string]$WorkspaceName,

    [Parameter(Mandatory = $false)]
    [ValidateSet("push", "pull", "auto")]
    [string]$Mode = "push"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "[sync] $Message"
}

function Get-PythonInvocation {
    param([string]$ScriptRoot)

    $venvPython = Join-Path $ScriptRoot ".venv\Scripts\python.exe"
    if (Test-Path -LiteralPath $venvPython) {
        return @($venvPython)
    }

    $pythonCommand = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        return @($pythonCommand.Source)
    }

    $pyLauncher = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        return @($pyLauncher.Source, "-3")
    }

    throw "No Python interpreter was found. Install Python or create .venv before running this sync script."
}

function Ensure-Directory {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Get-WorkspaceUri {
    param([string]$Path)
    $resolved = (Resolve-Path -LiteralPath $Path).Path
    return [System.Uri]::new($resolved).AbsoluteUri
}

function Get-NormalizedPath {
    param([string]$Path)
    $resolved = (Resolve-Path -LiteralPath $Path).Path
    return ([System.IO.Path]::GetFullPath($resolved).TrimEnd("\\")).ToLowerInvariant()
}

function Convert-WorkspaceUriToNormalizedPath {
    param([string]$WorkspaceUri)

    if ([string]::IsNullOrWhiteSpace($WorkspaceUri)) {
        return $null
    }

    try {
        $uri = [System.Uri]$WorkspaceUri
        if (-not $uri.IsFile) {
            return $null
        }

        $localPath = $uri.LocalPath
        if ($localPath -match '^/[A-Za-z]:') {
            $localPath = $localPath.Substring(1)
        }

        return ([System.IO.Path]::GetFullPath($localPath).TrimEnd("\\")).ToLowerInvariant()
    }
    catch {
        return $null
    }
}

function Get-WorkspaceStorageEntry {
    param(
        [string]$WorkspaceStorageRoot,
        [string]$WorkspacePathNormalized
    )

    $entries = Get-ChildItem -LiteralPath $WorkspaceStorageRoot -Directory
    foreach ($entry in $entries) {
        $workspaceJson = Join-Path $entry.FullName "workspace.json"
        if (-not (Test-Path -LiteralPath $workspaceJson)) {
            continue
        }

        try {
            $json = Get-Content -LiteralPath $workspaceJson -Raw | ConvertFrom-Json
        }
        catch {
            continue
        }

        $folderPath = if ($json.PSObject.Properties.Name -contains "folder") {
            Convert-WorkspaceUriToNormalizedPath -WorkspaceUri $json.folder
        }
        else {
            $null
        }

        $configurationPath = if ($json.PSObject.Properties.Name -contains "configuration") {
            Convert-WorkspaceUriToNormalizedPath -WorkspaceUri $json.configuration
        }
        else {
            $null
        }

        if (($folderPath -and $folderPath -eq $WorkspacePathNormalized) -or
            ($configurationPath -and $configurationPath -eq $WorkspacePathNormalized)) {
            return $entry.FullName
        }
    }

    return $null
}

function Copy-DirectorySafe {
    param(
        [string]$Source,
        [string]$Destination,
        [switch]$MergeOnly
    )

    if (-not (Test-Path -LiteralPath $Source)) {
        Write-Step "skip missing directory: $Source"
        return
    }

    Ensure-Directory -Path $Destination
    $robocopyArgs = @(
        $Source,
        $Destination,
        "/E",
        "/R:1",
        "/W:1",
        "/NFL",
        "/NDL",
        "/NJH",
        "/NJS",
        "/NP"
    )

    if ($MergeOnly) {
        $robocopyArgs += "/XO"
    }

    & robocopy @robocopyArgs | Out-Null
    if ($LASTEXITCODE -gt 7) {
        throw "robocopy failed for $Source -> $Destination with exit code $LASTEXITCODE"
    }
}

function Copy-FileSafe {
    param(
        [string]$Source,
        [string]$Destination,
        [switch]$MergeOnly
    )

    if (-not (Test-Path -LiteralPath $Source)) {
        Write-Step "skip missing file: $Source"
        return
    }

    $destinationDir = Split-Path -Parent $Destination
    Ensure-Directory -Path $destinationDir

    if ($MergeOnly -and (Test-Path -LiteralPath $Destination)) {
        $sourceTime = (Get-Item -LiteralPath $Source).LastWriteTimeUtc
        $destinationTime = (Get-Item -LiteralPath $Destination).LastWriteTimeUtc
        if ($destinationTime -gt $sourceTime) {
            Write-Step "skip older file during merge: $Source"
            return
        }
    }

    Copy-Item -LiteralPath $Source -Destination $Destination -Force
}

function Get-PathLastWriteTimeUtc {
    param(
        [string]$Path,
        [ValidateSet("file", "directory")]
        [string]$Kind
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        return $null
    }

    if ($Kind -eq "file") {
        return (Get-Item -LiteralPath $Path).LastWriteTimeUtc
    }

    $latest = (Get-Item -LiteralPath $Path).LastWriteTimeUtc
    Get-ChildItem -LiteralPath $Path -Recurse -Force -ErrorAction SilentlyContinue | ForEach-Object {
        if ($_.LastWriteTimeUtc -gt $latest) {
            $latest = $_.LastWriteTimeUtc
        }
    }

    return $latest
}

function Resolve-SyncDirection {
    param(
        [string]$LocalPath,
        [string]$CloudPath,
        [ValidateSet("file", "directory")]
        [string]$Kind,
        [ValidateSet("push", "pull", "auto")]
        [string]$RequestedMode
    )

    if ($RequestedMode -ne "auto") {
        return $RequestedMode
    }

    $localExists = Test-Path -LiteralPath $LocalPath
    $cloudExists = Test-Path -LiteralPath $CloudPath

    if ($localExists -and -not $cloudExists) {
        return "push"
    }

    if ($cloudExists -and -not $localExists) {
        return "pull"
    }

    if (-not $localExists -and -not $cloudExists) {
        return $null
    }

    $localTime = Get-PathLastWriteTimeUtc -Path $LocalPath -Kind $Kind
    $cloudTime = Get-PathLastWriteTimeUtc -Path $CloudPath -Kind $Kind

    if ($null -eq $cloudTime) {
        return "push"
    }

    if ($null -eq $localTime) {
        return "pull"
    }

    if ($cloudTime -gt $localTime) {
        return "pull"
    }

    return "push"
}

function Invoke-SyncPair {
    param(
        [string]$LocalPath,
        [string]$CloudPath,
        [ValidateSet("file", "directory")]
        [string]$Kind,
        [ValidateSet("push", "pull", "auto")]
        [string]$Mode
    )

    $effectiveMode = Resolve-SyncDirection -LocalPath $LocalPath -CloudPath $CloudPath -Kind $Kind -RequestedMode $Mode
    if (-not $effectiveMode) {
        Write-Step "skip missing on both sides: $LocalPath"
        return
    }

    if ($effectiveMode -eq "push") {
        $source = $LocalPath
        $destination = $CloudPath
    }
    else {
        $source = $CloudPath
        $destination = $LocalPath
    }

    Write-Step "$effectiveMode $Kind :: $source -> $destination"

    if ($Kind -eq "directory") {
        Copy-DirectorySafe -Source $source -Destination $destination -MergeOnly:($Mode -eq "auto")
    }
    else {
        Copy-FileSafe -Source $source -Destination $destination -MergeOnly:($Mode -eq "auto")
    }
}

$workspacePathResolved = (Resolve-Path -LiteralPath $WorkspacePath).Path
$workspaceKey = if ($WorkspaceName) {
    $WorkspaceName
}
else {
    (Split-Path -Leaf $workspacePathResolved) -replace '[^A-Za-z0-9._-]+', '_'
}

$userRoot = Join-Path $env:APPDATA "Code\User"
$workspaceStorageRoot = Join-Path $userRoot "workspaceStorage"
$globalStorageRoot = Join-Path $userRoot "globalStorage"
$workspaceUri = Get-WorkspaceUri -Path $workspacePathResolved
$workspacePathNormalized = Get-NormalizedPath -Path $workspacePathResolved
$workspaceEntry = Get-WorkspaceStorageEntry -WorkspaceStorageRoot $workspaceStorageRoot -WorkspacePathNormalized $workspacePathNormalized

if (-not $workspaceEntry) {
    throw "No workspaceStorage entry was found for this workspace. Open the workspace once in VS Code, then run the script again. Workspace: $workspacePathResolved"
}

$cloudRootResolved = [System.IO.Path]::GetFullPath($CloudRoot)
$cloudBase = Join-Path $cloudRootResolved "vscode-copilot-sync"
$cloudWorkspace = Join-Path $cloudBase (Join-Path "workspaces" $workspaceKey)
$cloudUser = Join-Path $cloudBase "user"
$markdownExportRoot = Join-Path $cloudBase (Join-Path "chat-markdown" $workspaceKey)
$chatMarkdownScript = Join-Path $PSScriptRoot "export_copilot_chat_to_markdown.py"
[string[]]$pythonInvocation = @(Get-PythonInvocation -ScriptRoot $PSScriptRoot)

Ensure-Directory -Path $cloudWorkspace
Ensure-Directory -Path $cloudUser

$manifest = @{
    workspaceName = $workspaceKey
    workspacePath = $workspacePathResolved
    workspaceUri = $workspaceUri
    localWorkspaceStorageEntry = $workspaceEntry
    generatedAt = (Get-Date).ToString("s")
    machine = $env:COMPUTERNAME
    mode = $Mode
} | ConvertTo-Json -Depth 3

$manifestPath = Join-Path $cloudWorkspace "manifest.json"
if ($Mode -eq "push") {
    Set-Content -LiteralPath $manifestPath -Value $manifest -Encoding UTF8
}

$pairs = @(
    @{ Kind = "directory"; Local = (Join-Path $workspaceEntry "GitHub.copilot-chat"); Cloud = (Join-Path $cloudWorkspace "workspaceStorage\GitHub.copilot-chat") },
    @{ Kind = "directory"; Local = (Join-Path $workspaceEntry "chatSessions"); Cloud = (Join-Path $cloudWorkspace "workspaceStorage\chatSessions") },
    @{ Kind = "directory"; Local = (Join-Path $workspaceEntry "chatEditingSessions"); Cloud = (Join-Path $cloudWorkspace "workspaceStorage\chatEditingSessions") },
    @{ Kind = "directory"; Local = (Join-Path $globalStorageRoot "github.copilot-chat"); Cloud = (Join-Path $cloudUser "globalStorage\github.copilot-chat") },
    @{ Kind = "file"; Local = (Join-Path $userRoot "settings.json"); Cloud = (Join-Path $cloudUser "settings.json") },
    @{ Kind = "file"; Local = (Join-Path $userRoot "mcp.json"); Cloud = (Join-Path $cloudUser "mcp.json") },
    @{ Kind = "file"; Local = (Join-Path $userRoot "chatLanguageModels.json"); Cloud = (Join-Path $cloudUser "chatLanguageModels.json") }
)

$optionalPrompts = Join-Path $userRoot "prompts"
if ((Test-Path -LiteralPath $optionalPrompts) -or ($Mode -eq "pull" -and (Test-Path -LiteralPath (Join-Path $cloudUser "prompts")))) {
    $pairs += @{ Kind = "directory"; Local = $optionalPrompts; Cloud = (Join-Path $cloudUser "prompts") }
}

Write-Step "workspace key: $workspaceKey"
Write-Step "workspace URI: $workspaceUri"
Write-Step "workspace storage: $workspaceEntry"
Write-Step "cloud root: $cloudBase"
Write-Step "mode: $Mode"
Write-Step "Close VS Code before syncing to avoid active session database writes."

foreach ($pair in $pairs) {
    Invoke-SyncPair -LocalPath $pair.Local -CloudPath $pair.Cloud -Kind $pair.Kind -Mode $Mode
}

$cloudTranscriptRoot = Join-Path $cloudWorkspace "workspaceStorage\GitHub.copilot-chat\transcripts"
if (Test-Path -LiteralPath $chatMarkdownScript) {
    Ensure-Directory -Path $markdownExportRoot
    Write-Step "export chat transcripts to daily markdown: $markdownExportRoot"
    $pythonExecutable = $pythonInvocation[0]
    $pythonArguments = @()
    if ($pythonInvocation.Count -gt 1) {
        $pythonArguments = $pythonInvocation[1..($pythonInvocation.Count - 1)]
    }
    & $pythonExecutable @pythonArguments $chatMarkdownScript --transcripts-dir $cloudTranscriptRoot --output-dir $markdownExportRoot --workspace-name $workspaceKey --machine $env:COMPUTERNAME
    if ($LASTEXITCODE -ne 0) {
        throw "Markdown export script failed with exit code $LASTEXITCODE"
    }
}
else {
    Write-Step "skip markdown export because script was not found: $chatMarkdownScript"
}

if ($Mode -eq "pull") {
    Write-Step "Pull complete. Reopen the VS Code workspace so Copilot Chat can reload local state."
}
else {
    Write-Step "Push complete. Wait for your cloud client to sync $cloudBase to the cloud."
}