# Installation Guide

Complete setup instructions for the Smart Thermostat System v1.0.0.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Hardware Setup](#hardware-setup)
- [Arduino Setup](#arduino-setup)
- [Raspberry Pi Setup](#raspberry-pi-setup)
- [Configuration](#configuration)
- [Service Setup](#service-setup)
- [Testing](#testing)

## Prerequisites

### Hardware
- Arduino UNO (or compatible)
- Raspberry Pi 4 Model B or Pi 3B+
- 2x 5V Relay Modules
- 5V Power Supply (for relays, 2A+ recommended)
- USB Cable (Type A to Type B)
- MicroSD Card (16GB+, Class 10)
- Jumper wires
- Heating system with compatible interface

### Software
- Raspberry Pi OS (Lite recommended)
- Python 3.9 or higher
- Arduino IDE or Arduino CLI
- Telegram account
- Basic Linux command line knowledge

## Hardware Setup

### Wiring Diagram

```
Arduino UNO                    Relay Module
├─ Pin 5 (Digital) ──────────► IN1
├─ Pin 6 (Digital) ──────────► IN2
└─ GND ──────────────────────► GND

Relay Module                   Power & Heating
├─ VCC ──────────────────────► 5V Power Supply (+)
├─ GND ──────────────────────► 5V Power Supply (-) & Arduino GND
├─ COM ──────────────────────► Heating System Input
└─ NO ──────────────────────►  Heating System Output

Arduino                        Raspberry Pi
└─ USB Port ─────────────────► USB Port (any)
```

⚠️ **SAFETY WARNING**: 
- Turn OFF all power before wiring
- Use appropriate wire gauge for current
- Verify relay rating exceeds heater current  
- Keep high/low voltage wires separated
- **Consult a licensed electrician for mains connections**

## Arduino Setup

### Option 1: Using Arduino IDE (Easier)

1. **Install Arduino IDE**:
   - Download from https://www.arduino.cc/en/software
   - Install on your computer

2. **Install TimeLib library**:
   - Open Arduino IDE
   - Go to Sketch → Include Library → Manage Libraries
   - Search for "Time by Michael Margolis"
   - Click Install

3. **Upload sketch**:
   - Open `arduino_thermostat.ino`
   - Connect Arduino to computer via USB
   - Select Board: Tools → Board → Arduino UNO
   - Select Port: Tools → Port → (your Arduino port)
   - Click Upload button

### Option 2: Using Arduino CLI on Pi

```bash
# Install Arduino CLI
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh
export PATH=$PATH:~/bin

# Initialize
arduino-cli config init
arduino-cli core install arduino:avr
arduino-cli lib install "Time"

# Upload (replace PORT with your device)
arduino-cli compile --fqbn arduino:avr:uno arduino_thermostat.ino
arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:uno arduino_thermostat.ino
```

## Raspberry Pi Setup

### 1. Prepare Raspberry Pi

```bash
# Update system
sudo apt update && sudo apt full-upgrade -y

# Install dependencies
sudo apt install python3-pip python3-venv git -y

# Set timezone (adjust for your location)
sudo timedatectl set-timezone Europe/Istanbul

# Reboot
sudo reboot
```

### 2. Clone Repository

```bash
# Create project directory
cd ~
git clone https://github.com/yourusername/DIYThermostat.git thermostat-repo
cd thermostat-repo
```

### 3. Setup Python Environment

```bash
# Create virtual environment
python3 -m venv ~/thermostat-env

# Activate
source ~/thermostat-env/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 4. Find Arduino Port

```bash
# List serial devices
ls -la /dev/serial/by-id/

# Example output:
# /dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A50285BI-if00-port0

# Copy the full path for configuration
```

## Configuration

### 1. Create Environment File

```bash
# Copy example
cp .env.example ~/.env

# Edit configuration
nano ~/.env
```

### 2. Configure .env

```bash
# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Arduino Configuration
ARDUINO_PORT=/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_XXXXXX-if00-port0
BAUD_RATE=9600

# File Paths
LOG_FILE=/home/youruser/smart_thermostat.log
SCHEDULE_FILE=/home/youruser/schedule.json

# System Configuration
TIMEZONE=Europe/Istanbul
HEARTBEAT_TIMEOUT=90
HEARTBEAT_INTERVAL=30000
```

**Getting Telegram Credentials**:

1. Create bot via [@BotFather](https://t.me/botfather)
2. Send `/newbot` and follow prompts
3. Save bot token
4. Send a message to your bot
5. Get chat ID: `https://api.telegram.org/bot<TOKEN>/getUpdates`

### 3. Create Schedule File

```bash
# Copy example
cp schedule.json.example ~/schedule.json

# Edit schedules
nano ~/schedule.json
```

## Service Setup

### 1. Create Service Files

Create smart-thermostat.service:
```bash
sudo nano /etc/systemd/system/smart-thermostat.service
```

Paste:
```ini
[Unit]
Description=Smart Thermostat Manager
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/home/youruser
Environment="PATH=/home/youruser/thermostat-env/bin"
ExecStart=/home/youruser/thermostat-env/bin/python3 /home/youruser/smart_thermostat.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Create telegram-controller.service:
```bash
sudo nano /etc/systemd/system/telegram-controller.service
```

Paste:
```ini
[Unit]
Description=Telegram Controller for Thermostat
After=network.target smart-thermostat.service
Requires=smart-thermostat.service

[Service]
Type=simple
User=youruser
WorkingDirectory=/home/youruser
Environment="PATH=/home/youruser/thermostat-env/bin"
ExecStart=/home/youruser/thermostat-env/bin/python3 /home/youruser/telegram_controller.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Create thermostat-summary.service:
```bash
sudo nano /etc/systemd/system/thermostat-summary.service
```

Paste:
```ini
[Unit]
Description=Thermostat Summary Service
After=network.target smart-thermostat.service

[Service]
Type=simple
User=youruser
WorkingDirectory=/home/youruser
Environment="PATH=/home/youruser/thermostat-env/bin"
ExecStart=/home/youruser/thermostat-env/bin/python3 /home/youruser/summary.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Replace `youruser` with your actual username!**

### 2. Copy Python Files

```bash
cp ~/thermostat-repo/smart_thermostat.py ~/smart_thermostat.py
cp ~/thermostat-repo/telegram_controller.py ~/telegram_controller.py
cp ~/thermostat-repo/summary.py ~/summary.py
```

### 3. Enable and Start Services

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable smart-thermostat.service
sudo systemctl enable telegram-controller.service
sudo systemctl enable thermostat-summary.service

# Start services
sudo systemctl start smart-thermostat.service
sleep 3
sudo systemctl start telegram-controller.service
sudo systemctl start thermostat-summary.service

# Check status
sudo systemctl status smart-thermostat.service
sudo systemctl status telegram-controller.service
sudo systemctl status thermostat-summary.service
```

All three should show `active (running)` in green.

## Testing

### 1. Check Logs

```bash
# View smart-thermostat logs
sudo journalctl -u smart-thermostat.service -f

# Should see:
# - "Smart Thermostat Manager v1.0.0"
# - "Connected to Arduino"
# - "Time synced to Arduino"
# - "HEARTBEAT:HH:MM:OFF:AUTO"
```

### 2. Test Telegram Commands

Send to your bot:
- `/help` - Should show command list
- `/status` - Should show current status
- `/schedule` - Should show schedules

### 3. Test Manual Control

```
/off     # Turn off manually
/on      # Turn on manually
/auto    # Return to auto mode
```

### 4. Test Automatic Control

1. Edit schedule to start in 2 minutes:
   ```bash
   nano ~/schedule.json
   ```

2. Restart telegram-controller:
   ```bash
   sudo systemctl restart telegram-controller.service
   ```

3. Ensure AUTO mode:
   ```
   /auto
   ```

4. Wait for scheduled time - should receive notification!

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues.

## Updating

Use the provided update script:

```bash
cd ~
./update_thermostat.sh
```

Or manually:
```bash
cd ~/thermostat-repo
git pull
cp *.py ~/
sudo systemctl restart smart-thermostat.service telegram-controller.service
```

## Next Steps

- Configure your heating schedules
- Set up daily summaries
- Monitor logs for issues
- Enjoy automated heating! 🔥

