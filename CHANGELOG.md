# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-11-28

### Added
- **Socket-Based Architecture**: Clean separation between Arduino communication and Telegram interface
  - `smart_thermostat.py`: Exclusive Arduino serial port access, command server (port 5000)
  - `telegram_controller.py`: Telegram bot interface, notification server (port 5001)
  - Eliminates serial port conflicts and corrupted messages

- **AUTO Mode Notifications**: Automatic Telegram notifications when boiler starts/stops based on schedule
  - Real-time alerts with timestamp
  - Only for automatic events (not manual commands)

- **Systemd Service Management**: Reliable service orchestration
  - Proper service dependencies
  - Automatic restart on failure
  - Clean logging via journalctl

- **Schedule Management**:
  - Up to 5 concurrent heating schedules
  - Add, edit, delete schedules via Telegram
  - Dynamic schedule updates without restart
  - Persistent schedule storage in JSON format

- **Telegram Bot Commands**:
  - `/on` - Manual override ON
  - `/off` - Manual override OFF
  - `/auto` - Return to automatic schedule mode
  - `/status` - Real-time status from logs
  - `/schedule` - View current schedules
  - `/edit` - Modify existing schedule
  - `/add` - Add new schedule
  - `/delete` - Remove schedule
  - `/summary` - View runtime statistics
  - `/debug` - System debug information
  - `/help` - Command reference

- **Summary Service**: Runtime statistics and historical data
  - Daily, weekly runtime tracking
  - Session counting
  - Automated daily summaries

- **Robust Error Handling**:
  - Configuration validation on startup
  - Graceful degradation when services unavailable
  - Comprehensive logging

- **Documentation**:
  - Complete installation guide
  - Architecture documentation
  - Troubleshooting guide
  - Socket API documentation

### Fixed
- **Serial Port Conflict**: Resolved issue where multiple processes accessed Arduino simultaneously
- **Corrupted Messages**: Fixed garbled Arduino communications
- **Duplicate Processes**: Eliminated conflicts between screen sessions and systemd services
- **Time Synchronization**: Proper timezone handling for Turkey (UTC+3)

### Changed
- Migrated from screen-based deployment to systemd services
- Improved logging with structured messages
- Enhanced error messages for better debugging

### Technical Details
- Python 3.9+ (uses zoneinfo for timezone management)
- Arduino UNO with TimeLib
- Telegram Bot API via python-telegram-bot
- Socket-based inter-process communication
- JSON-based configuration

---

## Future Enhancements (Planned for v2.0)
- Temperature sensor integration
- Web dashboard interface
- Multi-zone heating control
- Weather API integration for smart scheduling
- Energy usage tracking
- Docker deployment option

---

[1.0.0]: https://github.com/yourusername/DIYThermostat/releases/tag/v1.0.0
