param([string]$LlmRoot = (Join-Path (Split-Path $PSScriptRoot -Parent) '..\prompt-llm'))
$ErrorActionPreference = 'Stop'
$LlmRoot = (Resolve-Path -LiteralPath $LlmRoot).Path
$model = Join-Path $LlmRoot 'models\qwen2.5-3b-instruct-q4_k_m.gguf'
$server = Join-Path $LlmRoot 'runtime\llama-server.exe'
$logs = Join-Path $LlmRoot 'logs'
New-Item -ItemType Directory -Force -Path $logs | Out-Null
function Test-PromptLlm {
    try {
        $models = Invoke-RestMethod 'http://127.0.0.1:1234/v1/models' -TimeoutSec 3
        return 'prompt-translator' -in $models.data.id
    } catch { return $false }
}
if (-not (Test-PromptLlm)) {
    if (-not (Test-Path -LiteralPath $server)) { throw "LLM runtime not found: $server" }
    if (-not (Test-Path -LiteralPath $model)) { throw "LLM model not found: $model" }
    $arguments = @('-m', ('"' + $model + '"'), '--alias', 'prompt-translator', '--host', '127.0.0.1', '--port', '1234', '-ngl', '0', '-c', '4096', '-t', '8', '--parallel', '1')
    $process = Start-Process -FilePath $server -ArgumentList $arguments -WorkingDirectory $LlmRoot -WindowStyle Hidden -RedirectStandardOutput "$logs\server.stdout.log" -RedirectStandardError "$logs\server.stderr.log" -PassThru
    $process.Id | Set-Content "$logs\server.pid"
    $ready = $false
    for ($attempt = 0; $attempt -lt 90; $attempt++) {
        if (Test-PromptLlm) { $ready = $true; break }
        if ($process.HasExited) { throw "Prompt LLM exited. Check $logs\server.stderr.log" }
        Start-Sleep -Seconds 2
    }
    if (-not $ready) { throw "Prompt LLM startup timed out. Check $logs" }
}
Write-Host 'Prompt LLM: http://127.0.0.1:1234/v1 (CPU)'
