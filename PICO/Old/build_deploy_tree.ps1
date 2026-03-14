$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$deploy = Join-Path $root 'Deploy'
$core = Join-Path $deploy 'Core'
$guild = Join-Path $deploy 'apps/guild_sim'
$sw = Join-Path $deploy 'apps/sw_digital'
$ovpet = Join-Path $deploy 'apps/open_vpet'
$rootLauncher = Join-Path $deploy 'Root'

New-Item -ItemType Directory -Force -Path $core | Out-Null
New-Item -ItemType Directory -Force -Path $guild | Out-Null
New-Item -ItemType Directory -Force -Path $sw | Out-Null
New-Item -ItemType Directory -Force -Path $ovpet | Out-Null
New-Item -ItemType Directory -Force -Path $rootLauncher | Out-Null

$coreFiles = @(
  'pc_menu.py','sd_setup.py','storage.py','kernel_core.py','game_paths.py',
  'ui_theme.py','integrity.py','collection_book.py','mission_log.py','reset_dev_data.py',
  'hardware_profiles.py','hardware_runtime.py','set_hardware_profile.py'
)
$guildFiles = @(
  'guild_sim_kernel.py','roster_manager.py','guild_rules.py','watch_system.py',
  'skills_catalog.py','seed_world.py'
)
$swFiles = @('sw25_kernel.py','sw25_math.py','campaign_stream.py')
$ovpetFiles = @('open_vpet_kernel.py')

foreach ($f in $coreFiles) {
  Copy-Item (Join-Path $root $f) -Destination (Join-Path $core $f) -Force
}
foreach ($f in $guildFiles) {
  Copy-Item (Join-Path $root $f) -Destination (Join-Path $guild $f) -Force
}
foreach ($f in $swFiles) {
  Copy-Item (Join-Path $root $f) -Destination (Join-Path $sw $f) -Force
}
foreach ($f in $ovpetFiles) {
  Copy-Item (Join-Path $root $f) -Destination (Join-Path $ovpet $f) -Force
}

# Keep app launchers deterministic for clean deploys.
Copy-Item (Join-Path $root 'guild_sim_main.py') -Destination (Join-Path $guild 'main.py') -Force
Copy-Item (Join-Path $root 'sw_digital_main.py') -Destination (Join-Path $sw 'main.py') -Force
Copy-Item (Join-Path $root 'open_vpet_main.py') -Destination (Join-Path $ovpet 'main.py') -Force

Copy-Item (Join-Path $root 'pico_root_boot.py') -Destination (Join-Path $rootLauncher 'boot.py') -Force
Copy-Item (Join-Path $root 'pico_root_main.py') -Destination (Join-Path $rootLauncher 'main.py') -Force

Write-Output 'Deploy tree refreshed.'
