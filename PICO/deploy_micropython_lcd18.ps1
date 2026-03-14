param(
    [string]$Port = "COM3"
)

$ErrorActionPreference = "Stop"

Write-Host "Deploying Pico-LCD-1.8 MicroPython files to $Port..."

mpremote connect $Port fs cp --force lcd.py :lcd.py
mpremote connect $Port fs cp --force st7735_1inch8.py :st7735_1inch8.py
mpremote connect $Port fs cp --force bmp24_stream.py :bmp24_stream.py
mpremote connect $Port fs cp --force show_uploaded_image_once.py :show_uploaded_image_once.py

# Keep both image paths available because different test scripts use different locations.
mpremote connect $Port fs mkdir :images
mpremote connect $Port fs cp --force chopper_160x128.bmp :chopper_160x128.bmp
mpremote connect $Port fs cp --force chopper_160x128.bmp :images/chopper_160x128.bmp

mpremote connect $Port exec "import machine; machine.soft_reset()"
mpremote connect $Port exec "import show_uploaded_image_once; show_uploaded_image_once.main()"

Write-Host "Done. If this fails with COM busy, close serial tools and rerun."
