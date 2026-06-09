# DGX Spark Remote Access

This guide records the working access path for the user's NVIDIA DGX Spark so future sessions can connect, inspect, and operate it without rediscovering the setup.

## Known Target

- Device: NVIDIA DGX Spark / GIGABYTE AI TOP ATOM
- Linux host: `aitopatom-36a9`
- LAN IP observed during setup: `172.30.1.87`
- SSH user: `bobeenlee`
- Primary interface observed on the device: `wlP9s9`
- DGX Dashboard service: bound on the device at `127.0.0.1:11000`

Do not commit passwords or private keys. Ask the user for the current password when an interactive SSH, sudo, RDP, or xrdp credential is needed.

## What Happened During First Setup

The sticker on the device showed an initial hotspot and setup address like:

```text
SSID: AITOPATOM-3649
URL: http://AITOPATOM-3649.local
```

After initial setup and update, that hotspot was no longer visible from the Control MacBook. The device appeared on the LAN as:

```text
aitopatom-36a9.local
172.30.1.87
```

The initial setup web UI on port `80` was available during onboarding, then stopped responding after setup completed. That is expected: the OS stayed alive and SSH remained reachable, while the temporary setup UI closed.

## Quick Status Check

From the Control MacBook:

```bash
ping -c 3 172.30.1.87
nc -vz -G 5 172.30.1.87 22
nc -vz -G 5 172.30.1.87 3389
curl -sS -i --max-time 5 http://172.30.1.87/
```

Expected steady state:

- SSH `22`: open
- HTTP `80`: usually closed after onboarding
- RDP `3389`: open if xrdp or GNOME Remote Desktop is enabled

SSH login:

```bash
ssh bobeenlee@172.30.1.87
```

Useful remote checks:

```bash
hostname
ip -brief addr
uptime
systemctl --no-pager --failed
nvidia-smi
ss -ltnp | grep -E ':(22|80|3389|11000)'
```

## DGX Dashboard

The DGX Dashboard service was observed running locally on the device:

```text
127.0.0.1:11000
```

Check it from SSH:

```bash
curl -sS -i --max-time 3 http://127.0.0.1:11000/ | head -40
systemctl --no-pager status dgx-dashboard dgx-dashboard-admin
```

Expose it to the Control MacBook with an SSH tunnel:

```bash
ssh -N -L 11000:127.0.0.1:11000 bobeenlee@172.30.1.87
```

Then open:

```text
http://127.0.0.1:11000/
```

Do not bind the dashboard externally unless the user explicitly asks.

## Remote Desktop

Two RDP paths were tested.

### GNOME Remote Desktop

GNOME Remote Desktop is present, but Windows App on macOS failed against the system GNOME RDP flow with logs like:

```text
[RDP] Sending server redirection
[DaemonSystem] Not found routing token on remote_clients list
ERRINFO_LOGOFF_BY_USER
```

If using GNOME Remote Desktop anyway, inspect status:

```bash
sudo grdctl --system status
systemctl --no-pager status gnome-remote-desktop.service
journalctl -u gnome-remote-desktop.service --no-pager -n 80
```

The system daemon needs readable TLS material owned by `gnome-remote-desktop`:

```bash
sudo mkdir -p /etc/gnome-remote-desktop
sudo openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout /etc/gnome-remote-desktop/rdp.key \
  -out /etc/gnome-remote-desktop/rdp.crt \
  -days 365 \
  -subj '/CN=aitopatom-36a9.local'
sudo chown gnome-remote-desktop:gnome-remote-desktop /etc/gnome-remote-desktop/rdp.key /etc/gnome-remote-desktop/rdp.crt
sudo chmod 600 /etc/gnome-remote-desktop/rdp.key
sudo chmod 644 /etc/gnome-remote-desktop/rdp.crt
```

Then configure, substituting credentials provided by the user at runtime:

```bash
sudo grdctl --system rdp set-tls-cert /etc/gnome-remote-desktop/rdp.crt
sudo grdctl --system rdp set-tls-key /etc/gnome-remote-desktop/rdp.key
sudo grdctl --system rdp set-credentials bobeenlee '<password>'
sudo grdctl --system rdp disable-port-negotiation
sudo grdctl --system rdp enable
sudo systemctl restart gnome-remote-desktop.service
```

If Windows App still fails with routing token or redirection errors, use xrdp instead.

### xrdp Fallback

xrdp avoids the GNOME Remote Desktop routing-token failure by creating an RDP/Xorg session directly.

Install:

```bash
sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y xrdp xorgxrdp
```

If `gnome-remote-desktop` already owns port `3389`, stop or disable it first:

```bash
sudo systemctl stop gnome-remote-desktop.service
sudo grdctl --system rdp disable || true
```

Fix the common xrdp TLS key permission issue:

```bash
sudo adduser xrdp ssl-cert
sudo systemctl restart xrdp xrdp-sesman
```

Make the user's RDP login start an Ubuntu GNOME session:

```bash
printf 'gnome-session --session=ubuntu\n' > ~/.xsession
chmod 600 ~/.xsession
```

Verify:

```bash
systemctl --no-pager status xrdp xrdp-sesman
ss -ltnp | grep -E ':(3389|3350)'
journalctl -u xrdp -u xrdp-sesman --no-pager -n 80
```

From Windows App or Microsoft Remote Desktop on the Control MacBook:

```text
PC name: 172.30.1.87
Username: bobeenlee
Password: ask the user
```

Prefer direct `172.30.1.87` access over an SSH tunnel for RDP. The direct port was reachable on the LAN, and tunneling through `127.0.0.1:<port>` made the GNOME RDP redirection path harder to diagnose.

## Browser Installation Note

The user's downloaded file was found at:

```text
/home/bobeenlee/다운로드/google-chrome-stable_current_amd64.deb
```

The DGX Spark is `arm64`, while that package is `amd64`:

```bash
dpkg --print-architecture
dpkg-deb -f /home/bobeenlee/다운로드/google-chrome-stable_current_amd64.deb Package Architecture Version
```

Do not install the amd64 Google Chrome `.deb` on this device. Use the arm64 Chromium snap instead:

```bash
sudo snap install chromium
command -v chromium
chromium --version
```

Observed working install:

```text
/snap/bin/chromium
Chromium 149.0.7827.53 snap
```

## Troubleshooting Signals

- `HTTP 80 connection refused`: usually the temporary onboarding UI is closed, not a dead device.
- `SSH 22 open but HTTP 80 closed`: OS is up; use SSH or dashboard tunnel.
- Windows App `0x207`: inspect server logs immediately; in the observed case, GNOME RDP redirection failed.
- xrdp log says `Cannot read private key file /etc/xrdp/key.pem: Permission denied`: add `xrdp` to `ssl-cert` and restart xrdp.
- `AITOPATOM-3649.local` does not resolve after setup: likely the initial hotspot is gone; use `aitopatom-36a9.local` or `172.30.1.87`.

## Safety

- Do not store or commit the user's SSH/RDP password.
- Keep RDP exposed only on trusted LANs. Prefer SSH tunnels for dashboard/admin web surfaces.
- Treat package installs and remote desktop daemon changes as `review-required` if they are part of a formal Hermes task.
