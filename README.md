
# Smart Thermostat System

A DIY smart thermostat system using Arduino UNO, Raspberry Pi 4, and Telegram bot for remote control. Control your heating system with scheduled automation and manual override via Telegram.

## Features

- ⏰ **Scheduled Heating**: Automatic on/off based on customizable schedules
- 📱 **Telegram Control**: Full control via Telegram bot commands
- 🔄 **Manual Override**: Switch between auto/manual modes anytime
- 📊 **Real-time Status**: Monitor thermostat state and temperature
- 🔧 **Dynamic Schedules**: Add/edit/delete schedules via Telegram
- 💾 **Persistent Settings**: Schedules saved in JSON format
- 🚨 **Offline Alerts**: Get notified if system goes offline
- 🌍 **Timezone Support**: Configured for Turkey (UTC+3)

## Hardware Requirements

- **Arduino UNO**
- **Raspberry Pi 4 Model B** (or compatible)
- **2x Dual Relay Modules** (JQC-3FF-S-Z)
- **USB Cable** (USB-A to USB-B for Arduino connection)
- **5V Power Supply** (for relays, separate from Arduino)
- **Jumper Wires**
- **Heating System** (e.g., Viessmann Vitodens 100-W)

## Software Requirements

- **Raspberry Pi OS Lite** (or full version)
- **Python 3.9+**
- **Arduino IDE** (or Arduino CLI)
- **Telegram Bot Token** (from @BotFather)

## System Architecture


Telegram Bot
     ↓
Raspberry Pi 4 (Orchestrator)
     ↓ (USB Serial)
Arduino UNO (Controller)
     ↓ (Relay Control)
Heating System

## Installation

### 1. Raspberry Pi Setup

#### Install Dependencies
```bash
# Update system
sudo apt update && sudo apt full-upgrade -y

# Install required packages
sudo apt install python3-pip python3-serial python3-venv git screen -y

# Create virtual environment
python3 -m venv ~/thermostat-env
source ~/thermostat-env/bin/activate

# Install Python packages
pip install pyserial requests python-telegram-bot pytz
```

#### Set Timezone
```bash
sudo timedatectl set-timezone Europe/Istanbul
```

### 2. Arduino Setup

#### Install Arduino CLI on Pi (Optional - for remote upload)
```bash
# Install Arduino CLI
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh
export PATH=$PATH:~/bin

# Initialize and install dependencies
arduino-cli config init
arduino-cli core install arduino:avr
arduino-cli lib install "Time"
```

#### Upload Arduino Code
1. Create sketch folder: `mkdir -p ~/arduino_thermostat`
2. Copy Arduino code to `~/arduino_thermostat/arduino_thermostat.ino`
3. Compile: `arduino-cli compile --fqbn arduino:avr:uno ~/arduino_thermostat`
4. Upload: `arduino-cli upload -p /dev/serial/by-id/[YOUR-DEVICE-ID] --fqbn arduino:avr:uno ~/arduino_thermostat`

### 3. Telegram Bot Setup

1. Create a bot via [@BotFather](https://t.me/botfather) on Telegram
2. Get your bot token
3. Get your chat ID by messaging the bot and visiting:
   ```
   https://api.telegram.org/bot[YOUR-BOT-TOKEN]/getUpdates
   ```
4. Update the configuration in both Python scripts

### 4. Configure Python Scripts

#### Create Main Controller (`smart_thermostat.py`)
```bash
nano ~/smart_thermostat.py
# Copy the smart_thermostat.py code
```

#### Create Telegram Controller (`telegram_controller.py`)
```bash
nano ~/telegram_controller.py
# Copy the telegram_controller.py code
```

#### Update Configuration
Edit both files and update:
- `TELEGRAM_BOT_TOKEN`: Your bot token
- `TELEGRAM_CHAT_ID`: Your chat ID
- `ARDUINO_PORT`: Your Arduino serial port
- `LOG_FILE`: Log file path

### 5. Create Schedule File
```bash
nano ~/schedule.json
```

```json
{
  "schedules": [
    {
      "name": "Morning",
      "startHour": 6,
      "startMinute": 0,
      "endHour": 8,
      "endMinute": 0
    },
    {
      "name": "Evening",
      "startHour": 17,
      "startMinute": 0,
      "endHour": 22,
      "endMinute": 0
    }
  ]
}
```

## Wiring Diagram

### Arduino Connections
```
Arduino UNO:
  Pin 5 (Digital) → Relay Module 1 (IN1)
  Pin 6 (Digital) → Relay Module 2 (IN2)
  GND → Relay Module GND
  USB → Raspberry Pi USB Port

Relay Module:
  VCC → 5V Power Supply
  GND → Common Ground (shared with Arduino)
  COM → Heating System Input
  NO → Heating System Output
  NC → (Not used)

Power:
  5V PSU → Relay VCC
  GND → Common Ground
```

### Safety Notes
⚠️ **WARNING**: Working with mains voltage is dangerous!
- Turn OFF main power before wiring
- Use proper wire gauge for current rating
- Ensure relay rating exceeds heater current
- Keep high/low voltage wires separated
- Consider using a professional electrician

## Running the System

### Start with Screen (Recommended)
```bash
# Start main controller
screen -dmS thermostat bash -c 'source ~/thermostat-env/bin/activate && python3 ~/smart_thermostat.py'

# Start Telegram controller
screen -dmS telegram bash -c 'source ~/thermostat-env/bin/activate && python3 ~/telegram_controller.py'

# View screens
screen -ls

# Attach to screen
screen -r thermostat  # or screen -r telegram

# Detach from screen
# Press Ctrl+A, then D
```

### Alternative: Systemd Services

#### Create service for smart_thermostat
```bash
sudo nano /etc/systemd/system/smart-thermostat.service
```

```ini
[Unit]
Description=Smart Thermostat Manager
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi
ExecStart=/home/pi/thermostat-env/bin/python3 /home/pi/smart_thermostat.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Create service for telegram_controller
```bash
sudo nano /etc/systemd/system/telegram-controller.service
```

```ini
[Unit]
Description=Telegram Controller
After=network.target smart-thermostat.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi
ExecStart=/home/pi/thermostat-env/bin/python3 /home/pi/telegram_controller.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Enable and start services
```bash
sudo systemctl daemon-reload
sudo systemctl enable smart-thermostat.service telegram-controller.service
sudo systemctl start smart-thermostat.service telegram-controller.service
```

## Telegram Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/on` | Turn thermostat ON manually | `/on` |
| `/off` | Turn thermostat OFF manually | `/off` |
| `/auto` | Return to automatic schedule mode | `/auto` |
| `/status` | Check current status (live from logs) | `/status` |
| `/schedule` | View all schedules | `/schedule` |
| `/edit` | Modify existing schedule | `/edit 1 06 00 08 00` |
| `/add` | Add new schedule (max 5) | `/add 14 00 16 00 Afternoon` |
| `/delete` | Remove a schedule | `/delete 2` |
| `/debug` | Show system debug info | `/debug` |
| `/help` | Show all commands | `/help` |

## File Structure

```
~/
├── smart_thermostat.py        # Main controller (Arduino communication)
├── telegram_controller.py     # Telegram bot handler
├── schedule.json              # Schedule configuration
├── smart_thermostat.log       # System log file
├── thermostat-env/           # Python virtual environment
└── arduino_thermostat/       # Arduino sketch folder
    └── arduino_thermostat.ino
```

## Troubleshooting

### Arduino Not Responding
```bash
# Check if Arduino is connected
ls /dev/serial/by-id/

# Find the correct port
dmesg | grep tty

# Update ARDUINO_PORT in Python scripts
```

### Time Sync Issues
- Arduino shows wrong time: Check timezone offset in Arduino code (UTC+3 for Turkey)
- Time drifts: System automatically resyncs every hour

### Telegram Commands Not Working
```bash
# Check if services are running
screen -ls

# Restart services
screen -X -S telegram quit
screen -X -S thermostat quit
# Then start again with screen commands above
```

### Upload to Arduino Fails
1. Stop Python scripts first (they hold the serial port)
2. Upload the code
3. Restart Python scripts

### System Goes Offline
- Check USB connection
- Check power supply to relays
- Review logs: `tail -f ~/smart_thermostat.log`

## Monitoring

### View Logs
```bash
# Real-time log monitoring
tail -f ~/smart_thermostat.log

# View last 50 lines
tail -n 50 ~/smart_thermostat.log
```

### Check Screen Sessions
```bash
# List all screens
screen -ls

# Attach to thermostat screen
screen -r thermostat

# Attach to telegram screen
screen -r telegram
```

## Security Notes

⚠️ **IMPORTANT**: 
- **NEVER** share your Telegram bot token publicly
- Revoke and regenerate token if exposed
- Keep your Raspberry Pi updated
- Use strong passwords
- Consider firewall rules for Pi

## System Behavior

### Automatic Operation
1. System checks time every second
2. Compares with configured schedules
3. Turns heating ON/OFF automatically
4. Sends Telegram notification on state change
5. Logs all activities

### Manual Override
- `/on` or `/off` commands override schedule
- System stays in manual mode until `/auto` is sent
- Manual state persists through schedule times

### Heartbeat Monitoring
- Arduino sends heartbeat every 30 seconds
- Pi monitors heartbeat
- Alert sent if no heartbeat for 90 seconds
- "Back online" notification when connection restored

## Contributing

Feel free to fork and improve the system. Some ideas:
- Add temperature sensor support
- Web interface
- Multiple zone control
- Weather API integration
- Energy usage tracking

## License

This project is open source and available under the MIT License.

## Acknowledgments

- Arduino TimeLib library
- python-telegram-bot library
- The open source community

## Support

For issues or questions, please create an issue on GitHub or contact via Telegram bot commands.

---

**Disclaimer**: This project involves mains electricity. Improper installation can cause fire, injury, or death. Always consult with a qualified electrician for mains voltage connections.
