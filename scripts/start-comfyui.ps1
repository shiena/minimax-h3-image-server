param([string]$ComfyRoot = 'D:\ComfyUI')
$ErrorActionPreference = 'Stop'
$repo = Split-Path $PSScriptRoot -Parent
$logs = Join-Path $repo 'logs'
if (-not (Test-Path -LiteralPath "$ComfyRoot\.venv\Scripts\python.exe")) {
    throw "ComfyUI Python environment not found: $ComfyRoot"
}
if (-not (Test-Path -LiteralPath "$ComfyRoot\custom_nodes\minimax_h3\__init__.py")) {
    throw "H3 custom node not found in $ComfyRoot\custom_nodes\minimax_h3"
}
New-Item -ItemType Directory -Force -Path $logs | Out-Null
$env:PYTHONUTF8 = '1'

function Test-LocalServer([string]$Url) {
    try {
        $null = Invoke-RestMethod -Uri $Url -TimeoutSec 3
        return $true
    } catch { return $false }
}

& "$PSScriptRoot\start-api.ps1"
if (-not (Test-LocalServer 'http://127.0.0.1:8188/system_stats')) {
    $comfy = Start-Process -FilePath "$ComfyRoot\.venv\Scripts\python.exe" -ArgumentList @('main.py', '--listen', '127.0.0.1', '--port', '8188', '--disable-auto-launch', '--offline') -WorkingDirectory $ComfyRoot -WindowStyle Hidden -RedirectStandardOutput "$logs\comfy.stdout.log" -RedirectStandardError "$logs\comfy.stderr.log" -PassThru
    $comfy.Id | Set-Content "$logs\comfy.pid"
}
foreach ($url in @('http://127.0.0.1:8188/system_stats')) {
    $ready = $false
    for ($attempt = 0; $attempt -lt 120; $attempt++) {
        if (Test-LocalServer $url) { $ready = $true; break }
        if ($comfy -and $comfy.HasExited) { throw "ComfyUI exited with code $($comfy.ExitCode). Check $logs\comfy.stderr.log" }
        Start-Sleep -Seconds 2
    }
    if (-not $ready) { throw "Server startup timed out: $url. Check $logs" }
}
$nodes = Invoke-RestMethod 'http://127.0.0.1:8188/object_info/MiniMaxH3Image' -TimeoutSec 10
if (-not $nodes.MiniMaxH3Image) { throw 'ComfyUI did not load the MiniMaxH3Image node. Check logs\comfy.stderr.log' }
Write-Host 'ComfyUI: http://127.0.0.1:8188'
Write-Host 'Workflow: MiniMax H3 Image'
