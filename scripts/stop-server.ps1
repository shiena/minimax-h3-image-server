# Shared process validation for the local server stop commands.
function Stop-LocalServer {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [int]$Port,
        [string]$Name,
        [string]$CommandPattern,
        [string]$ExecutablePattern,
        [string]$PidFile
    )
    $listeners = @(Get-NetTCPConnection -State Listen -ErrorAction Stop |
        Where-Object { $_.LocalPort -eq $Port })
    if (-not $listeners.Count) {
        Write-Host "$Name is already stopped."
        return
    }
    $processIds = @($listeners.OwningProcess | Sort-Object -Unique)
    $targets = @()
    foreach ($processId in $processIds) {
        $target = Get-CimInstance Win32_Process -Filter "ProcessId=$processId" -ErrorAction Stop
        if (-not $target -or $target.CommandLine -notmatch $CommandPattern -or
            $target.ExecutablePath -notmatch $ExecutablePattern) {
            throw "Port $Port is owned by an unexpected process ($processId). Nothing was stopped."
        }
        $targets += $target
    }
    foreach ($target in $targets) {
        if ($PSCmdlet.ShouldProcess("$Name (PID $($target.ProcessId), port $Port)", 'Stop server')) {
            # Recheck identity because a PID may be reused between inspection and shutdown.
            $current = Get-CimInstance Win32_Process -Filter "ProcessId=$($target.ProcessId)" -ErrorAction Stop
            if (-not $current) { continue }
            if ($current.CreationDate -ne $target.CreationDate -or
                $current.CommandLine -ne $target.CommandLine -or
                $current.ExecutablePath -ne $target.ExecutablePath) {
                throw "Process identity changed for $Name. Run the stop command again."
            }
            Stop-Process -Id $target.ProcessId -ErrorAction Stop
            Wait-Process -Id $target.ProcessId -Timeout 15 -ErrorAction SilentlyContinue
            if (Get-Process -Id $target.ProcessId -ErrorAction SilentlyContinue) {
                throw "$Name did not stop within 15 seconds."
            }
            Write-Host "$Name stopped."
        }
    }
    if (-not $WhatIfPreference -and (Test-Path -LiteralPath $PidFile)) {
        $remaining = @(Get-NetTCPConnection -State Listen -ErrorAction Stop |
            Where-Object { $_.LocalPort -eq $Port })
        if (-not $remaining.Count) { Remove-Item -LiteralPath $PidFile }
    }
}
