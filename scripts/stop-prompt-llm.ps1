[CmdletBinding(SupportsShouldProcess)]
param([string]$LlmRoot = (Join-Path (Split-Path $PSScriptRoot -Parent) '..\prompt-llm'))
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\stop-server.ps1"
$server = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath((Join-Path $LlmRoot 'runtime\llama-server.exe'))
Stop-LocalServer -Port 1234 -Name 'Prompt LLM' `
    -CommandPattern '(?i)--alias\s+prompt-translator\s.*--port\s+1234(?:\s|$)' `
    -ExecutablePattern ('(?i)^' + [regex]::Escape($server) + '$') `
    -PidFile (Join-Path $LlmRoot 'logs\server.pid')
