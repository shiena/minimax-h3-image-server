[CmdletBinding(SupportsShouldProcess)]
param()
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\stop-server.ps1"
$repo = Split-Path $PSScriptRoot -Parent
Stop-LocalServer -Port 8633 -Name 'H3 API' `
    -CommandPattern '(?i)\s-m\s+uvicorn\s+app\.main:app\s.*--port\s+8633(?:\s|$)' `
    -ExecutablePattern '(?i)[\\/]python(?:w)?\.exe$' `
    -PidFile "$repo\logs\server.pid"
