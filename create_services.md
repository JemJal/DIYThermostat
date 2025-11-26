## Architecture Overview

**IMPORTANT**: The system uses socket communication to prevent serial port conflicts:
- `smart_thermostat.py` - Communicates with Arduino via serial, listens on port 5000 for commands
- `telegram_controller.py` - Sends commands to smart_thermostat.py via socket (port 5000)
- `smart_thermostat.py` MUST start before `telegram_controller.py`

---

```bash
# Create service file for smart_thermostat
sudo nano /etc/systemd/system/smart-thermostat.service
```

Paste this:

```ini
[Unit]
Description=Smart Thermostat Manager
After=network.target

[Service]
Type=simple
User=cem
WorkingDirectory=/home/cem
Environment="PATH=/home/cem/thermostat-env/bin"
ExecStart=/home/cem/thermostat-env/bin/python3 /home/cem/smart_thermostat.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Save with `Ctrl+X`, `Y`, `Enter`.

---

```bash
# Create service file for telegram_controller
sudo nano /etc/systemd/system/telegram-controller.service
```

Paste this (NOTE: depends on smart-thermostat.service):

```ini
[Unit]
Description=Telegram Controller for Thermostat
After=network.target smart-thermostat.service
Requires=smart-thermostat.service

[Service]
Type=simple
User=cem
WorkingDirectory=/home/cem
Environment="PATH=/home/cem/thermostat-env/bin"
ExecStart=/home/cem/thermostat-env/bin/python3 /home/cem/telegram_controller.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Save with `Ctrl+X`, `Y`, `Enter`.

---

```bash
# Create service file for summary
sudo nano /etc/systemd/system/thermostat-summary.service
```

Paste this:

```ini
[Unit]
Description=Thermostat Summary Service
After=network.target smart-thermostat.service

[Service]
Type=simple
User=cem
WorkingDirectory=/home/cem
Environment="PATH=/home/cem/thermostat-env/bin"
ExecStart=/home/cem/thermostat-env/bin/python3 /home/cem/summary.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Save with `Ctrl+X`, `Y`, `Enter`.

---

## Enable and Start Services

```bash
# Reload systemd daemon
sudo systemctl daemon-reload

# Enable all services to start on boot
sudo systemctl enable smart-thermostat.service
sudo systemctl enable telegram-controller.service
sudo systemctl enable thermostat-summary.service

# Start all services now
sudo systemctl start smart-thermostat.service
sudo systemctl start telegram-controller.service
sudo systemctl start thermostat-summary.service

# Check status of all services
sudo systemctl status smart-thermostat.service
sudo systemctl status telegram-controller.service
sudo systemctl status thermostat-summary.service
```

---

## Useful Commands

```bash
# Check if services are running
sudo systemctl is-active smart-thermostat.service

# View logs for a service
sudo journalctl -u smart-thermostat.service -f

# View last 50 lines of logs
sudo journalctl -u smart-thermostat.service -n 50

# Restart a service
sudo systemctl restart smart-thermostat.service

# Stop a service
sudo systemctl stop smart-thermostat.service

# Start a service
sudo systemctl start smart-thermostat.service

# View all running services
systemctl list-units --type=service --state=running
```

---

## Stop Screen Sessions (No Longer Needed)

```bash
# Kill all screen sessions
screen -ls | grep -oP '\d+\.\w+' | xargs -I {} screen -X -S {} quit

# Verify screens are gone
screen -ls
```

---

## Test Auto-Start

```bash
# Reboot the Pi
sudo reboot

# After reboot, check if services started automatically
sudo systemctl status smart-thermostat.service
sudo systemctl status telegram-controller.service
sudo systemctl status thermostat-summary.service
```

All three should show `active (running)`.

---

## Verify Everything Works

```bash
# Check logs
sudo journalctl -u smart-thermostat.service -n 20
sudo journalctl -u telegram-controller.service -n 20
sudo journalctl -u thermostat-summary.service -n 20

# Test Telegram command
# Send /status to your bot - should work
```

	