# Start the local H3 API in the background, or reuse the running server.
$ErrorActionPreference = 'Stop'
$repo = Split-Path $PSScriptRoot -Parent
$logs = Join-Path $repo 'logs'
$python = Join-Path $repo '.venv\Scripts\python.exe'
$url = 'http://127.0.0.1:8633'

function Test-H3Server {
    try {
        $health = Invoke-RestMethod "$url/api/health" -TimeoutSec 3
        return ($health.status -eq 'ok' -and $health.model -eq 'MiniMaxAI/MiniMax-H3-Image')
    } catch { return $false }
}

if (-not (Test-H3Server)) {
    if (-not (Test-Path -LiteralPath $python)) { throw "Python environment not found: $python" }
    New-Item -ItemType Directory -Force -Path $logs | Out-Null
    $env:PYTHONUTF8 = '1'
    $h3 = Start-Process -FilePath $python -ArgumentList @('-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8633') -WorkingDirectory $repo -WindowStyle Hidden -RedirectStandardOutput "$logs\server.stdout.log" -RedirectStandardError "$logs\server.stderr.log" -PassThru
    $h3.Id | Set-Content "$logs\server.pid"
    $ready = $false
    for ($attempt = 0; $attempt -lt 120; $attempt++) {
        if (Test-H3Server) { $ready = $true; break }
        if ($h3.HasExited) { throw "H3 exited with code $($h3.ExitCode). Check $logs\server.stderr.log" }
        Start-Sleep -Seconds 2
    }
    if (-not $ready) { throw "H3 startup timed out. Check $logs\server.stderr.log" }
}
Write-Host "H3 API: $url"
Write-Host "API documentation: $url/docs"
