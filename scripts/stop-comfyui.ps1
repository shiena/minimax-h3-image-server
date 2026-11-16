[CmdletBinding(SupportsShouldProcess)]
param([string]$ComfyRoot = 'D:\ComfyUI')
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\stop-server.ps1"
$repo = Split-Path $PSScriptRoot -Parent
Stop-LocalServer -Port 8188 -Name 'ComfyUI' `
    -CommandPattern '(?i)(?:\s|["\\/])main\.py"?\s.*--port\s+8188(?:\s|$)' `
    -ExecutablePattern '(?i)[\\/]python(?:w)?\.exe$' `
    -PidFile "$repo\logs\comfy.pid"
& "$PSScriptRoot\stop-api.ps1"
$comfyPath = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($ComfyRoot)
$llmRoot = Join-Path (Split-Path $comfyPath -Parent) 'prompt-llm'
& "$PSScriptRoot\stop-prompt-llm.ps1" -LlmRoot $llmRoot
