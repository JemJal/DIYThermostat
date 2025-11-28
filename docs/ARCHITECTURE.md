# System Architecture

Technical documentation for DIY Thermostat v1.0.0

## Overview

The system uses a clean socket-based architecture to separate concerns and prevent conflicts.

## Components

### 1. Arduino UNO (`arduino_thermostat.ino`)
- **Role**: Hardware controller, schedule execution, relay management
- **Communication**: Serial (USB) to Raspberry Pi
- **Functions**:
  - Stores up to 5 schedules in memory
  - Executes schedule logic in AUTO mode
  - Controls relay pins (5, 6) for heating
  - Sends heartbeat every 30 seconds
  - Reports status changes
  - Handles manual overrides

### 2. Smart Thermostat (`smart_thermostat.py`)
- **Role**: Arduino interface, exclusive serial port owner
- **Ports**:
  - Command Server: 5000 (receives commands)
  - Notification Client: 5001 (sends notifications)
- **Functions**:
  - Connects to Arduino via serial
  - Syncs time every hour
  - Monitors heartbeat
  - Executes commands from telegram_controller
  - Sends notification requests for AUTO mode events
  - Logs all Arduino communication

### 3. Telegram Controller (`telegram_controller.py`)
- **Role**: User interface, Telegram bot, notification sender
- **Ports**:
  - Command Client: 5000 (sends to smart_thermostat)
  - Notification Server: 5001 (receives requests)
- **Functions**:
  - Handles Telegram bot commands
  - Manages schedule.json file
  - Sends commands to Arduino via smart_thermostat
  - Receives notification requests
  - Sends Telegram messages

### 4. Summary Service (`summary.py`)
- **Role**: Statistics calculation, data persistence
- **Port**: 9999 (summary request server)
- **Functions**:
  - Parses log files
  - Calculates runtime statistics
  - Manages daily summaries
  - Provides historical data

## Communication Flow

### Command Flow (User → Arduino)

```
User sends /on via Telegram
    ↓
telegram_controller.py receives command
    ↓
telegram_controller sends "OVERRIDE:ON" to port 5000
    ↓
smart_thermostat.py receives command
    ↓
smart_thermostat sends "OVERRIDE:ON\n" to Arduino serial
    ↓
Arduino executes command, activates relays
    ↓
Arduino sends "STATUS:STARTED_MANUAL"
    ↓
smart_thermostat logs the event
```

### Notification Flow (Arduino → User)

```
Arduino detects schedule time, activates relays
    ↓
Arduino sends "STATUS:STARTED" via serial
    ↓
smart_thermostat.py receives message
    ↓
smart_thermostat sends notification request to port 5001
    {"type": "notification", "message": "🔥 Boiler Started..."}
    ↓
telegram_controller.py receives request on port 5001
    ↓
telegram_controller sends Telegram message
    ↓
User receives notification on phone
```

## Socket Protocol

### Port 5000: Command Protocol
**Direction**: telegram_controller → smart_thermostat

**Commands**:
- `OVERRIDE:ON` - Turn on manually
- `OVERRIDE:OFF` - Turn off manually
- `OVERRIDE:AUTO` - Return to auto mode
- `CLEAR_SCHED` - Clear all schedules
- `SCHED:idx:sh:sm:eh:em` - Update schedule
- `GET_STATUS` - Request current status

**Response** (JSON):
```json
{
  "status": "success",
  "message": "Command sent: OVERRIDE:ON"
}
```

### Port 5001: Notification Protocol
**Direction**: smart_thermostat → telegram_controller

**Request** (JSON):
```json
{
  "type": "notification",
  "message": "🔥 Boiler Started\n\n⏰ Time: 06:00\n🔄 Mode: AUTO"
}
```

**Response** (JSON):
```json
{
  "status": "success",
  "message": "Notification sent"
}
```

### Port 9999: Summary Protocol
**Direction**: telegram_controller → summary service

**Commands**:
- `SUMMARY` - Get current summary
- `DAILY_SUMMARY` - Save today's summary
- `HISTORICAL` - Get all historical data

## Arduino Protocol

### Messages from Pi to Arduino

```
TIME:<unix_timestamp>           # Set Arduino time (UTC)
OVERRIDE:ON                      # Manual on
OVERRIDE:OFF                     # Manual off
OVERRIDE:AUTO                    # Return to schedule
SCHED:<idx>:<sh>:<sm>:<eh>:<em> # Update schedule
CLEAR_SCHED                      # Clear all schedules
STATUS                          # Request status
GET_SCHEDULES                   # Request schedule list
```

### Messages from Arduino to Pi

```
READY                                    # Arduino startup
TIME_SYNC_REQUEST                        # Request time
TIME_SET:<timestamp>:<HH>:<MM>           # Time confirmed
STATUS:STARTED                           # Started (AUTO)
STATUS:STOPPED                           # Stopped (AUTO)
STATUS:STARTED_MANUAL                    # Started (MANUAL)
STATUS:STOPPED_MANUAL                    # Stopped (MANUAL)
MODE:AUTO                                # Mode changed
MODE:MANUAL_ON                           # Mode changed
MODE:MANUAL_OFF                          # Mode changed
HEARTBEAT:<HH>:<MM>:<status>:<mode>     # Periodic heartbeat
SCHED_UPDATED:<idx>:<sh>:<sm>-<eh>:<em> # Schedule confirmed
SCHEDULES_CLEARED                        # Schedules cleared
ERROR:<message>                          # Error occurred
```

## State Management

### Arduino States
- **Mode**: AUTO, MANUAL_ON, MANUAL_OFF
- **Status**: ON, OFF
- **Time Set**: true/false
- **Schedules**: Array of 5 schedules with active flags

### Python State
- **Last Heartbeat**: Timestamp of last Arduino message
- **Thermostat Status**: ON/OFF from last update
- **Thermostat Mode**: AUTO/MANUAL_ON/MANUAL_OFF
- **Alert Sent**: Flag for offline alert

## Design Decisions

### Why Socket Communication?
1. **Prevents Serial Port Conflicts**: Only one process owns serial port
2. **Clean Separation**: Each process has single responsibility
3. **Reliability**: Connection errors don't crash other processes
4. **Scalability**: Easy to add more services
5. **Testability**: Can test components independently

### Why Systemd Services?
1. **Automatic Restart**: Services restart on failure
2. **Boot Integration**: Start on system boot
3. **Logging**: Centralized via journalctl
4. **Dependencies**: Proper startup order
5. **Resource Management**: Process supervision

### Why Separate Notification Port?
1. **Bidirectional**: Both processes can initiate communication
2. **Non-Blocking**: Notifications don't block commands
3. **Independent**: Notification failure doesn't affect control
4. **Clean**: Separation of command and event flows

## Error Handling

### Serial Port Errors
- Reconnection with exponential backoff
- Continued operation if Arduino temporarily disconnected
- Automatic time resync on reconnection

### Socket Errors
- Graceful degradation (notifications fail silently)
- Command retries with timeout
- Log warnings but continue operation

### Configuration Errors
- Validate on startup
- Exit with clear error message
- Prevent partial startup

## Performance

- **Heartbeat Interval**: 30 seconds
- **Time Sync**: Every hour
- **Socket Timeout**: 2-5 seconds
- **Schedule Check**: Every loop (~100ms)
- **Relay Response**: < 100ms

## Security Considerations

1. **Local Sockets**: Only localhost, not exposed
2. **No Authentication**: Trusted local communication
3. **Input Validation**: Commands validated before execution
4. **Telegram Token**: Stored in .env, never committed
5. **Serial Access**: Only one authorized process

## Monitoring

### Logs Location
- **smart_thermostat**: `~/smart_thermostat.log` + journalctl
- **telegram_controller**: journalctl only
- **summary**: `~/thermostat_summary.log` + journalctl

### Health Checks
- Heartbeat monitoring (90s timeout)
- Service status via systemctl
- Log analysis for errors

## Future Enhancements

Planned for v2.0:
- Temperature sensor feedback
- PID control algorithm
- Multiple zone support
- Web dashboard
- MQTT integration
- Energy monitoring

