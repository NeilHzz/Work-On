# LS-DYNA Parametric Batch Run Script
# Runs 8 cases from chicken_parametric, outputs to chicken_results\{case}\

$LSDYNA      = "D:\Program Files\ANSYS Inc\v231\ansys\bin\winx64\lsdyna_dp.exe"
$BASE_DIR    = "D:\system_folder\Desktop\LS-DYNA\chicken_parametric"
$RESULTS_DIR = "D:\system_folder\Desktop\LS-DYNA\chicken_results"
$NCPU        = 24

$CASES = @(
    "pos_p1_p1",
    "pos_p1_n1",
    "pos_n1_p1",
    "pos_n1_n1",
    "pos_p0_p1",
    "pos_p0_n1",
    "pos_p1_p0",
    "pos_n1_p0"
)

$total    = $CASES.Count
$startAll = Get-Date
New-Item -ItemType Directory -Path $RESULTS_DIR -Force | Out-Null
$log = Join-Path $RESULTS_DIR "batch_run.log"

"[$startAll] Batch run started. Total cases: $total" | Tee-Object -FilePath $log
"Results dir: $RESULTS_DIR" | Tee-Object -FilePath $log -Append

foreach ($i in 0..($total - 1)) {
    $case   = $CASES[$i]
    $srcDir = Join-Path $BASE_DIR $case
    $inputK = Join-Path $srcDir "input.k"

    if (-not (Test-Path $inputK)) {
        "[SKIP] $case - input.k not found" | Tee-Object -FilePath $log -Append
        continue
    }

    $runDir = Join-Path $RESULTS_DIR $case
    New-Item -ItemType Directory -Path $runDir -Force | Out-Null
    Copy-Item $inputK -Destination $runDir -Force

    $idx   = $i + 1
    $start = Get-Date
    "====================================================" | Tee-Object -FilePath $log -Append
    "[$start] ($idx/$total) Starting: $case" | Tee-Object -FilePath $log -Append
    "  Run dir: $runDir  NCPU: $NCPU" | Tee-Object -FilePath $log -Append
    "====================================================" | Tee-Object -FilePath $log -Append

    Push-Location $runDir
    & $LSDYNA i=input.k S=input.intfor x=70 NCPU=$NCPU
    $exit = $LASTEXITCODE
    Pop-Location

    $end     = Get-Date
    $elapsed = ($end - $start).ToString("hh\:mm\:ss")
    $status  = if ($exit -eq 0) { "DONE" } else { "FAILED (exit $exit)" }
    "[$end] $case - $status  elapsed: $elapsed" | Tee-Object -FilePath $log -Append
}

$endAll    = Get-Date
$totalTime = ($endAll - $startAll).ToString("hh\:mm\:ss")
"[$endAll] All cases finished. Total time: $totalTime" | Tee-Object -FilePath $log -Append
Write-Host "Log saved: $log" -ForegroundColor Cyan
