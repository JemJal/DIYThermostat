# Smart Thermostat System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/yourusername/DIYThermostat/releases)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

A DIY smart thermostat system using Arduino UNO, Raspberry Pi 4, and Telegram bot for complete heating control. Features scheduled automation, manual override, real-time notifications, and a clean socket-based architecture.

## ✨ Features

- **⏰ Scheduled Heating**: Automatic on/off based on up to 5 customizable schedules
- **📱 Full Telegram Control**: Control everything via Telegram bot commands
- **🔔 Real-Time Notifications**: Get alerted when boiler starts/stops automatically
- **🔄 Manual Override**: Switch between AUTO/MANUAL modes anytime
- **📊 Live Status Monitoring**: Check thermostat state and temperature in real-time
- **🔧 Dynamic Schedule Management**: Add/edit/delete schedules via Telegram
- **💾 Persistent Settings**: All schedules saved and survive restarts
- **📈 Runtime Statistics**: Track daily, weekly heating usage
- **🏗️ Clean Architecture**: Socket-based communication prevents conflicts
- **🛡️ Reliable**: Systemd service management with auto-restart

## 🚀 Quick Start

### Prerequisites
- Arduino UNO
- Raspberry Pi 4 (or 3B+)
- 2x Relay Modules (5V)
- USB Cable (Arduino to Pi)
- Telegram Bot Token

### Installation (5 steps)

1. **Flash Arduino**:
   ```bash
   # Upload arduino_thermostat.ino to your Arduino UNO
   ```

2. **Setup Raspberry Pi**:
   ```bash
   # Clone repository
   git clone https://github.com/yourusername/DIYThermostat.git
   cd DIYThermostat

   # Install dependencies
   python3 -m venv thermostat-env
   source thermostat-env/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure**:
   ```bash
   # Copy example configuration
   cp .env.example ~/.env
   cp schedule.json.example ~/schedule.json

   # Edit with your settings
   nano ~/.env
   ```

4. **Setup Services**:
   ```bash
   # See docs/INSTALLATION.md for detailed systemd setup
   sudo systemctl enable smart-thermostat.service telegram-controller.service
   sudo systemctl start smart-thermostat.service telegram-controller.service
   ```

5. **Test**:
   ```
   # Send /status command to your Telegram bot
   ```

**Full installation guide**: [docs/INSTALLATION.md](docs/INSTALLATION.md)

## 📋 System Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────┐
│  Telegram Bot   │ ◄─────► │   Raspberry Pi   │ ◄─────► │  Arduino    │
│   (User App)    │         │                  │  Serial │    UNO      │
└─────────────────┘         │  ┌────────────┐  │         │             │
                            │  │telegram_   │  │         │  Schedule   │
        Commands            │  │controller  │  │         │  Logic      │
          &                 │  └─────┬──────┘  │         │             │
      Notifications         │        │         │         │   Relays    │
                            │  Socket│5001     │         │   (5,6)     │
                            │        │         │         └──────┬──────┘
                            │  ┌─────▼──────┐  │                │
                            │  │smart_      │  │                │
                            │  │thermostat  │  │         ┌──────▼──────┐
                            │  └────────────┘  │         │   Heating   │
                            │                  │         │   System    │
                            └──────────────────┘         └─────────────┘
```

**Key Design**:
- **smart_thermostat.py**: Exclusive Arduino communication
- **telegram_controller.py**: Telegram interface only
- **Socket communication**: Clean separation, no conflicts
- **systemd services**: Reliable, auto-restart

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for technical details.

## 💬 Telegram Commands

| Command | Description |
|---------|-------------|
| `/on` | Turn heating ON manually |
| `/off` | Turn heating OFF manually |
| `/auto` | Return to automatic schedule mode |
| `/status` | Check current status |
| `/schedule` | View all schedules |
| `/edit 1 06 00 08 00` | Modify schedule #1 |
| `/add 14 00 16 00 Afternoon` | Add new schedule |
| `/delete 2` | Remove schedule #2 |
| `/summary` | View runtime statistics |
| `/help` | Show all commands |

## 📊 Example Schedule

Create `~/schedule.json`:

```json
{
  "schedules": [
    {
      "name": "Morning Warmup",
      "startHour": 6,
      "startMinute": 0,
      "endHour": 8,
      "endMinute": 30
    },
    {
      "name": "Evening Heating",
      "startHour": 17,
      "startMinute": 0,
      "endHour": 22,
      "endMinute": 0
    }
  ]
}
```

## 🔌 Wiring

```
Arduino UNO:
  Pin 5 (Digital) → Relay Module 1 (IN1)
  Pin 6 (Digital) → Relay Module 2 (IN2)
  GND → Relay Module GND
  USB → Raspberry Pi USB Port

Relay Module:
  VCC → 5V Power Supply (separate)
  GND → Common Ground
  COM → Heating System Input
  NO → Heating System Output
```

⚠️ **WARNING**: Working with mains voltage is dangerous! Consult a qualified electrician.

## 📱 Notifications

Get automatic alerts when your heating turns on/off:

```
🔥 Boiler Started

⏰ Time: 06:00
🔄 Mode: AUTO
```

Only for automatic events (not manual commands).

## 🛠️ Troubleshooting

**Common issues**:

1. **"No heartbeat" errors**: Check USB connection and Arduino power
2. **Schedules not working**: Ensure you sent `/auto` command
3. **Services won't start**: Check `.env` file exists at `~/.env`
4. **Corrupted messages**: Make sure only one process accesses Arduino

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for detailed solutions.

## 📚 Documentation

- **[Installation Guide](docs/INSTALLATION.md)** - Detailed setup instructions
- **[Architecture](docs/ARCHITECTURE.md)** - Technical details and design
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common problems and solutions
- **[API Documentation](docs/API.md)** - Socket protocol for developers
- **[CHANGELOG](CHANGELOG.md)** - Version history

## 🔒 Security Notes

- **Never commit `.env` file** - Contains credentials
- Keep Raspberry Pi updated: `sudo apt update && sudo apt upgrade`
- Use strong bot tokens - regenerate if compromised
- Consider firewall rules for Pi

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Arduino TimeLib library
- python-telegram-bot library
- The open source community

## ⚡ System Requirements

**Hardware**:
- Arduino UNO (or compatible)
- Raspberry Pi 4 Model B (or Pi 3B+)
- 2x 5V Relay Modules
- 5V Power Supply for relays
- USB cable (A to B)

**Software**:
- Raspberry Pi OS (Lite or full)
- Python 3.9+
- Arduino IDE (for flashing)
- Telegram account

## 📊 Statistics

Example runtime report:

```
📊 Thermostat Runtime Summary

📅 Today (2025-11-28):
   ⏱️ 4h 30m (3 sessions)

📅 Yesterday (2025-11-27):
   ⏱️ 5h 15m (4 sessions)

📊 Last 7 Days:
   ⏱️ 32h 20m (25 sessions)
   📈 Average: 4h 37m/day
```

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/DIYThermostat/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/DIYThermostat/discussions)
- **Documentation**: [docs/](docs/)

## ⚠️ Disclaimer

This project involves mains electricity. Improper installation can cause fire, injury, or death. Always consult with a qualified electrician for mains voltage connections. Use at your own risk.

---

**Made with ❤️ by Cem** | [Report Bug](https://github.com/yourusername/DIYThermostat/issues) | [Request Feature](https://github.com/yourusername/DIYThermostat/issues)
