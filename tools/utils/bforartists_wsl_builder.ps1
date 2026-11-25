# SPDX-FileCopyrightText: 2026 Bforartists Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

<#
.SYNOPSIS
  Windows side of the Linux builder: WSL memory settings, first-time setup and the weekly task.

.DESCRIPTION
  Pairs with tools/utils/bforartists_linux_builder.sh, which does the real work inside WSL.

    setup       Sizes WSL for Bforartists builds (.wslconfig: memory + swap), then runs the
                builder's `setup` in your WSL distro (installs tools, clones the source).
    image       Installs the Rocky 8 build toolchain in WSL (once, about 30-60 minutes).
    run         Runs one weekly build now (update + build + package + upload).
    schedule    Registers the weekly Windows task "Bforartists Linux devbuild".
    unschedule  Removes that task.
    status      Shows the WSL distro, the task and the builder status.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File tools\utils\bforartists_wsl_builder.ps1 setup
  powershell -ExecutionPolicy Bypass -File tools\utils\bforartists_wsl_builder.ps1 schedule -Day Saturday -Time 18:00
#>

param(
  [Parameter(Position = 0)]
  [ValidateSet('setup', 'image', 'run', 'schedule', 'unschedule', 'status')]
  [string]$Action = 'status',
  [string]$Distro = '',                 # default: the first Rocky/Ubuntu/Debian distro found
  [string]$Day = 'Saturday',
  [string]$Time = '18:00',
  [int]$MemoryGB = 0,                   # default: 75% of the PC's RAM
  [int]$SwapGB = 32,
  [string]$SwapFile = '',               # e.g. Z:\WSL\swap.vhdx (default: WSL puts it on C:)
  [string]$DevbuildsRemote = ''         # e.g. bfa-devbuilds:bforartists-devbuilds (rclone remote in WSL)
)

$ErrorActionPreference = 'Stop'
$TaskName = 'Bforartists Linux devbuild'
$Builder = '~/bfa/bin/bforartists_linux_builder.sh'

function Say($icon, $text) { Write-Host "$icon  $text" }

function Get-BuilderDistro {
  if ($Distro) { return $Distro }
  # wsl.exe prints UTF-16; strip the NUL characters.
  $names = (wsl.exe --list --quiet) -replace "`0", '' | Where-Object { $_.Trim() }
  $pick = $names | Where-Object { $_ -match 'Rocky|Ubuntu|Debian' } | Select-Object -First 1
  if (-not $pick) { throw "No Rocky/Ubuntu/Debian WSL distro found. Pass -Distro <name>." }
  return $pick.Trim()
}

function Invoke-InWsl($distro, $command) {
  wsl.exe -d $distro -- bash -lc $command
  if ($LASTEXITCODE -ne 0) { throw "WSL command failed ($LASTEXITCODE): $command" }
}

function Set-WslConfig {
  $path = Join-Path $env:USERPROFILE '.wslconfig'
  $ramGB = [math]::Floor((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB)
  $mem = if ($MemoryGB -gt 0) { $MemoryGB } else { [math]::Floor($ramGB * 0.75) }
  $text = if (Test-Path $path) { Get-Content $path -Raw } else { '' }
  if ($text -match '(?m)^\s*memory\s*=' -and $text -match '(?m)^\s*swap\s*=' -and
      (-not $SwapFile -or $text -match '(?m)^\s*swapFile\s*=')) {
    Say '✅' "Keeping your existing .wslconfig memory/swap settings ($path)"
    return $false
  }
  if ($text) { Copy-Item $path "$path.bak" -Force; Say '💾' "Backed up $path to .wslconfig.bak" }
  if ($text -notmatch '(?m)^\[wsl2\]') { $text = $text.TrimEnd() + "`r`n[wsl2]`r`n" }
  $add = @()
  if ($text -notmatch '(?m)^\s*memory\s*=') { $add += "memory=${mem}GB" }
  if ($text -notmatch '(?m)^\s*swap\s*=') { $add += "swap=${SwapGB}GB" }
  if ($SwapFile -and $text -notmatch '(?m)^\s*swapFile\s*=') { $add += "swapFile=$($SwapFile -replace '\\', '\\')" }
  $text = $text -replace '(?m)^\[wsl2\]\s*$', ("[wsl2]`r`n" + ($add -join "`r`n"))
  Set-Content -Path $path -Value $text.TrimEnd() -Encoding ASCII
  Say '🧠' "WSL may now use ${mem} GB of your ${ramGB} GB RAM, plus ${SwapGB} GB swap ($path)"
  return $true
}

$d = Get-BuilderDistro
Say '🐧' "WSL distro: $d"

switch ($Action) {
  'setup' {
    $changed = Set-WslConfig
    if ($changed) {
      Say '🔁' 'Restarting WSL so the new memory settings apply (closes open WSL windows)'
      wsl.exe --shutdown
    }
    # Run the builder straight from this checkout; its setup copies itself into ~/bfa/bin.
    # (Line endings are normalised first, in case Git checked the file out with CRLF.)
    $winScript = Join-Path $PSScriptRoot 'bforartists_linux_builder.sh'
    $wslScript = ((wsl.exe -d $d -- wslpath -a ($winScript -replace '\\', '/')) -replace "`0", '').Trim()
    Invoke-InWsl $d "sed 's/\r`$//' '$wslScript' > /tmp/bforartists_linux_builder.sh && bash /tmp/bforartists_linux_builder.sh setup"
    Say '✅' 'Setup done. Next: build the image (once):  .\tools\utils\bforartists_wsl_builder.ps1 image'
  }
  'image' { Invoke-InWsl $d "$Builder image" }
  'run' {
    $envs = if ($DevbuildsRemote) { "BFA_DEVBUILDS_REMOTE='$DevbuildsRemote' " } else { '' }
    Invoke-InWsl $d "$envs$Builder weekly"
  }
  'schedule' {
    $envs = if ($DevbuildsRemote) { "BFA_DEVBUILDS_REMOTE='$DevbuildsRemote' " } else { '' }
    $action = New-ScheduledTaskAction -Execute 'wsl.exe' -Argument "-d $d -- bash -lc `"$envs$Builder weekly`""
    $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $Day -At $Time
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopIfGoingOnBatteries `
      -AllowStartIfOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 12)
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings `
      -Description 'Weekly Linux devbuild of Bforartists in WSL (tools/utils/bforartists_linux_builder.sh)' -Force | Out-Null
    Say '⏰' "Scheduled '$TaskName': every $Day at $Time (runs while you're signed in)"
    if (-not $DevbuildsRemote) { Say 'ℹ️' 'No -DevbuildsRemote given: tarballs stay in WSL (~/bfa/build_output/tar).' }
  }
  'unschedule' {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Say '🗑️' "Removed '$TaskName'"
  }
  'status' {
    $t = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($t) {
      $info = $t | Get-ScheduledTaskInfo
      Say '⏰' "Task: $($t.State) · next $($info.NextRunTime) · last $($info.LastRunTime) (result $($info.LastTaskResult))"
    } else { Say '⏰' 'Task: not scheduled' }
    Invoke-InWsl $d "[ -x $Builder ] && $Builder status || echo 'Builder not set up yet: run setup'"
  }
}
