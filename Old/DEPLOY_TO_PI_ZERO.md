# VS Code-Only Deploy To Raspberry Pi Zero W

This workflow does not require Thonny.

This deploy script now uses a single streamed upload (`tar | ssh`) so password prompt count is minimized.

## 1. Prepare Pi Zero W

On Pi Zero (once):

```bash
sudo apt update
sudo apt install -y python3 openssh-server
sudo systemctl enable ssh
sudo systemctl start ssh
```

Optional: enable SSH from Raspberry Pi Imager before first boot.

## 2. Connect Pi Zero to Monitor

- Boot Pi Zero W with monitor attached.
- Log into Raspberry Pi OS desktop or terminal.
- Confirm Python works:

```bash
python3 --version
```

## 3. Deploy From VS Code Terminal (Windows)

From your project folder:

```powershell
.\deploy_to_pi_zero.ps1 -Host raspberrypi.local -User pi -TargetDir ~/open-guild-sim -App all

Note: current script parameter name is `-PiHost`.

```powershell
.\deploy_to_pi_zero.ps1 -PiHost raspberrypi.local -User pi -TargetDir ~/open-guild-sim -App all
```
```

If mDNS doesn't resolve, use IP address:

```powershell
.\deploy_to_pi_zero.ps1 -Host 192.168.1.50 -User pi -TargetDir ~/open-guild-sim -App all

```powershell
.\deploy_to_pi_zero.ps1 -PiHost 192.168.1.50 -User pi -TargetDir ~/open-guild-sim -App all

If you still want zero password prompts, set up SSH keys once:

```powershell
ssh-keygen -t ed25519
type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh pi@raspberrypi.local "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```
```
```

## 4. Run On Pi Zero (Monitor)

Option A: run via SSH command from VS Code terminal

```powershell
ssh pi@raspberrypi.local "cd ~/open-guild-sim && python3 main.py"
```

Option B: run directly in terminal on Pi monitor

```bash
cd ~/open-guild-sim
python3 main.py
```

## 5. Notes

- This runs the terminal UI on Pi Zero monitor.
- Storage uses local folder fallback (`sd` or `data`) on Linux.
- For an always-on kiosk style, create a systemd service later.
