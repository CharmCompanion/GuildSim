param(
    [string]$OutDir = ".\\deploy",
    [switch]$IncludeSaves
)

$ErrorActionPreference = "Stop"

$coreDir = Join-Path $OutDir "pico_core"
$sdDir = Join-Path $OutDir "sd_card"

New-Item -ItemType Directory -Path $coreDir -Force | Out-Null
New-Item -ItemType Directory -Path $sdDir -Force | Out-Null

$coreFiles = @(
    "main.py",
    "guild_sim_main.py",
    "bmp24_stream.py",
    "pico_app.py",
    "pico_assets.py",
    "pico_input.py",
    "pico_sprites.py",
    "models.py",
    "lcd.py",
    "st7735_1inch8.py"
)

foreach ($f in $coreFiles) {
    if (Test-Path $f) {
        Copy-Item $f -Destination (Join-Path $coreDir $f) -Force
    }
}

if ($IncludeSaves -and (Test-Path ".\\saves")) {
    Copy-Item ".\\saves" -Destination (Join-Path $coreDir "saves") -Recurse -Force
}

$sdItems = @("assets", "static", "templates", "Old", "attached_assets")
foreach ($item in $sdItems) {
    if (Test-Path $item) {
        Copy-Item $item -Destination (Join-Path $sdDir $item) -Recurse -Force
    }
}

Write-Host "Staged Pico core at: $coreDir"
Write-Host "Staged SD payload at:  $sdDir"
