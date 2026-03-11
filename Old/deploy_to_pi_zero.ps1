param(
  [string]$PiHost = "raspberrypi.local",
  [string]$User = "pi",
  [string]$TargetDir = "~/open-guild-sim",
  [ValidateSet("all","guild_sim","sw_digital","open_vpet")]
  [string]$App = "all"
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$remote = "$User@$PiHost"

$coreFiles = @(
  'pc_menu.py','sd_setup.py','storage.py','kernel_core.py','game_paths.py',
  'ui_theme.py','integrity.py','collection_book.py','mission_log.py',
  'hardware_profiles.py','hardware_runtime.py','set_hardware_profile.py',
  'reset_dev_data.py','main.py'
)

$guildFiles = @(
  'guild_sim_kernel.py','roster_manager.py','guild_rules.py','watch_system.py',
  'skills_catalog.py','seed_world.py'
)

$swFiles = @('sw25_kernel.py','sw25_math.py','campaign_stream.py')
$ovpetFiles = @('open_vpet_kernel.py')

function Add-UniqueFiles {
  param(
    [string[]]$Base,
    [string[]]$NewItems
  )
  foreach ($item in $NewItems) {
    if ($Base -notcontains $item) {
      $Base += $item
    }
  }
  return ,$Base
}

$filesToDeploy = @()
$filesToDeploy = Add-UniqueFiles -Base $filesToDeploy -NewItems $coreFiles

if ($App -eq 'all' -or $App -eq 'guild_sim') {
  $filesToDeploy = Add-UniqueFiles -Base $filesToDeploy -NewItems $guildFiles
}
if ($App -eq 'all' -or $App -eq 'sw_digital') {
  $filesToDeploy = Add-UniqueFiles -Base $filesToDeploy -NewItems $swFiles
}
if ($App -eq 'all' -or $App -eq 'open_vpet') {
  $filesToDeploy = Add-UniqueFiles -Base $filesToDeploy -NewItems $ovpetFiles
}

if ($filesToDeploy.Count -eq 0) {
  throw "No files selected for deployment."
}

Write-Output "Deploying $($filesToDeploy.Count) files to Pi Zero: $TargetDir"
foreach ($f in $filesToDeploy) {
  Write-Output "  - $f"
}

# Expand ~/ on remote side in a shell-safe way.
$remoteTarget = if ($TargetDir.StartsWith('~/')) {
  '$HOME/' + $TargetDir.Substring(2)
} else {
  $TargetDir
}

$remoteCommand = "mkdir -p '$remoteTarget' && tar -xzf - -C '$remoteTarget'"
& tar -czf - -C $root @filesToDeploy | ssh $remote $remoteCommand

if ($LASTEXITCODE -ne 0) {
  throw "Deployment failed during tar stream upload."
}

Write-Output "Deployment complete."
Write-Output "Run on Pi Zero:"
Write-Output "  ssh $remote \"cd $TargetDir && python3 main.py\""
