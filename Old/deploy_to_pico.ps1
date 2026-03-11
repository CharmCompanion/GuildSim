param(
  [string]$Port = "COM3",
  [ValidateSet("guild_sim","sw_digital","open_vpet","all")]
  [string]$App = "guild_sim",
  [switch]$Clean
)

$ErrorActionPreference = 'Stop'
$py = 'C:/Users/RY0M/AppData/Local/Programs/Python/Python312/python.exe'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

function Invoke-Mpremote {
  param(
    [Parameter(Mandatory = $true)]
    [string[]]$Args,
    [Parameter(Mandatory = $true)]
    [string]$Step,
    [switch]$AllowFileExists,
    [switch]$AllowMissing
  )

  $output = & $py -m mpremote @Args 2>&1

  $outputText = ""
  if ($output) {
    $outputText = ($output | Out-String)
  }

  if ($LASTEXITCODE -ne 0) {
    if ($AllowFileExists -and ($outputText -match 'File exists')) {
      Write-Output "Skipping existing target for step: $Step"
      return
    }
    if ($AllowMissing -and ($outputText -match 'No such file|does not exist|ENOENT')) {
      Write-Output "Skipping missing target for step: $Step"
      return
    }

    if ($output) {
      $output | ForEach-Object { Write-Output $_ }
    }
    throw "mpremote failed at step: $Step"
  }

  if ($output) {
    $output | ForEach-Object { Write-Output $_ }
  }
}

# Ensure deploy tree is up to date.
& "$root/build_deploy_tree.ps1"

$core = Join-Path $root 'Deploy/Core'
$rootLaunch = Join-Path $root 'Deploy/Root'
$apps = @()
if ($App -eq 'all') {
  $apps = @('guild_sim', 'sw_digital', 'open_vpet')
} else {
  $apps = @($App)
}

Write-Output "Connecting to $Port"

try {
  Invoke-Mpremote -Args @('connect', $Port, 'exec', 'print(1)') -Step 'port check'
} catch {
  Write-Error "Unable to access $Port. Close Thonny (or switch Thonny interpreter to Local Python) and retry."
  throw
}

if ($Clean) {
  Write-Output "Clean deploy enabled: removing target folders before upload."

  if ($App -eq 'all') {
    Invoke-Mpremote -Args @('connect', $Port, 'fs', '--recursive', 'rm', ':/apps/guild_sim') -Step 'clean guild_sim app folder' -AllowMissing
    Invoke-Mpremote -Args @('connect', $Port, 'fs', '--recursive', 'rm', ':/apps/sw_digital') -Step 'clean sw_digital app folder' -AllowMissing
    Invoke-Mpremote -Args @('connect', $Port, 'fs', '--recursive', 'rm', ':/apps/open_vpet') -Step 'clean open_vpet app folder' -AllowMissing
    Invoke-Mpremote -Args @('connect', $Port, 'fs', '--recursive', 'rm', ':/Core') -Step 'clean Core folder' -AllowMissing
  } else {
    Invoke-Mpremote -Args @('connect', $Port, 'fs', '--recursive', 'rm', ":/apps/$App") -Step "clean $App app folder" -AllowMissing
    Invoke-Mpremote -Args @('connect', $Port, 'fs', '--recursive', 'rm', ':/Core') -Step 'clean Core folder' -AllowMissing
  }
}

# Create target directories on Pico.
Invoke-Mpremote -Args @('connect', $Port, 'fs', 'mkdir', ':/Core') -Step 'mkdir Core' -AllowFileExists
Invoke-Mpremote -Args @('connect', $Port, 'fs', 'mkdir', ':/apps') -Step 'mkdir apps' -AllowFileExists

# Copy core files.
Get-ChildItem $core -File | ForEach-Object {
  $src = $_.FullName
  $dst = ":/Core/$($_.Name)"
  Write-Output "Copy core: $($_.Name)"
  Invoke-Mpremote -Args @('connect', $Port, 'fs', '--force', 'cp', $src, $dst) -Step "copy core $($_.Name)"
}

# Copy root launcher files (boot.py/main.py).
Get-ChildItem $rootLaunch -File | ForEach-Object {
  $src = $_.FullName
  $dst = ":/$($_.Name)"
  Write-Output "Copy root launcher: $($_.Name)"
  Invoke-Mpremote -Args @('connect', $Port, 'fs', '--force', 'cp', $src, $dst) -Step "copy root launcher $($_.Name)"
}

foreach ($appName in $apps) {
  $appPath = Join-Path $root "Deploy/apps/$appName"
  Invoke-Mpremote -Args @('connect', $Port, 'fs', 'mkdir', ":/apps/$appName") -Step "mkdir app $appName" -AllowFileExists

  # Copy app files.
  Get-ChildItem $appPath -File | ForEach-Object {
    $src = $_.FullName
    $dst = ":/apps/$appName/$($_.Name)"
    Write-Output "Copy app ($appName): $($_.Name)"
    Invoke-Mpremote -Args @('connect', $Port, 'fs', '--force', 'cp', $src, $dst) -Step "copy $appName $($_.Name)"
  }
}

Write-Output "Upload complete."
Write-Output "Run app with:"
if ($App -eq 'all') {
  Write-Output ("  {0} -m mpremote connect {1} exec ""import sys; sys.path.append('/Core'); exec(open('/apps/guild_sim/main.py').read())""" -f $py, $Port)
  Write-Output ("  {0} -m mpremote connect {1} exec ""import sys; sys.path.append('/Core'); exec(open('/apps/sw_digital/main.py').read())""" -f $py, $Port)
  Write-Output ("  {0} -m mpremote connect {1} exec ""import sys; sys.path.append('/Core'); exec(open('/apps/open_vpet/main.py').read())""" -f $py, $Port)
} else {
  Write-Output ("  {0} -m mpremote connect {1} exec ""import sys; sys.path.append('/Core'); exec(open('/apps/{2}/main.py').read())""" -f $py, $Port, $App)
}
