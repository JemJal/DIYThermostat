# API Documentation

Socket communication protocol for Smart Thermostat System v1.0.0

## Overview

The system uses TCP sockets for inter-process communication between Python services.

## Ports

| Port | Direction | Purpose |
|------|-----------|---------|
| 5000 | telegram_controller → smart_thermostat | Send commands to Arduino |
| 5001 | smart_thermostat → telegram_controller | Send notification requests |
| 9999 | telegram_controller → summary | Request statistics |

All sockets are localhost-only (127.0.0.1) for security.

## Port 5000: Command Protocol

### Connection
```python
import socket
import json

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('localhost', 5000))
```

### Commands

#### OVERRIDE:ON
Turn heating on manually.

**Request**: `OVERRIDE:ON`

**Response**:
```json
{
  "status": "success",
  "message": "Command sent: OVERRIDE:ON"
}
```

#### OVERRIDE:OFF
Turn heating off manually.

**Request**: `OVERRIDE:OFF`

**Response**:
```json
{
  "status": "success",
  "message": "Command sent: OVERRIDE:OFF"
}
```

#### OVERRIDE:AUTO
Return to automatic schedule mode.

**Request**: `OVERRIDE:AUTO`

**Response**:
```json
{
  "status": "success",
  "message": "Command sent: OVERRIDE:AUTO"
}
```

#### CLEAR_SCHED
Clear all schedules from Arduino.

**Request**: `CLEAR_SCHED`

**Response**:
```json
{
  "status": "success",
  "message": "Schedules cleared"
}
```

#### SCHED
Update a schedule on Arduino.

**Request**: `SCHED:0:6:0:8:30`

Format: `SCHED:<index>:<startHour>:<startMin>:<endHour>:<endMin>`
- index: 0-4 (5 total slots)
- Hours: 0-23 (24-hour format)
- Minutes: 0-59

**Response**:
```json
{
  "status": "success",
  "message": "Schedule sent: SCHED:0:6:0:8:30"
}
```

#### GET_STATUS
Query current thermostat status.

**Request**: `GET_STATUS`

**Response**:
```json
{
  "status": "success",
  "thermostat_status": "ON",
  "thermostat_mode": "AUTO",
  "last_heartbeat": 1732627800.123
}
```

### Error Responses

**Arduino not connected**:
```json
{
  "status": "error",
  "message": "Failed to send to Arduino"
}
```

**Invalid command**:
```json
{
  "status": "error",
  "message": "Unknown command: INVALID"
}
```

### Example Usage

```python
import socket
import json

def send_command(command):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(5)
    client.connect(('localhost', 5000))
    client.sendall(command.encode('utf-8'))
    response = client.recv(4096).decode('utf-8')
    client.close()
    return json.loads(response)

# Turn on
result = send_command("OVERRIDE:ON")
print(result)

# Get status
status = send_command("GET_STATUS")
print(f"Thermostat is {status['thermostat_status']}")
```

## Port 5001: Notification Protocol

### Connection
```python
import socket
import json

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('localhost', 5001))
```

### Request Format

```json
{
  "type": "notification",
  "message": "🔥 Boiler Started\n\n⏰ Time: 06:00\n🔄 Mode: AUTO"
}
```

### Response

**Success**:
```json
{
  "status": "success",
  "message": "Notification sent"
}
```

**Error**:
```json
{
  "status": "error",
  "message": "Failed to send notification"
}
```

### Example Usage

```python
import socket
import json

def request_notification(message):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(2)
    client.connect(('localhost', 5001))
    
    notification_data = {
        "type": "notification",
        "message": message
    }
    
    client.sendall(json.dumps(notification_data).encode('utf-8'))
    response = client.recv(1024).decode('utf-8')
    client.close()
    
    return json.loads(response)

# Send notification
result = request_notification("Test notification")
print(result)
```

## Port 9999: Summary Protocol

### Commands

#### SUMMARY
Get current runtime summary.

**Request**: `SUMMARY`

**Response**:
```json
{
  "status": "success",
  "timestamp": "2025-11-28T15:30:00",
  "today": {
    "date": "2025-11-28",
    "runtime_seconds": 16200,
    "runtime_formatted": "4h 30m",
    "sessions": 3
  },
  "yesterday": {
    "date": "2025-11-27",
    "runtime_seconds": 18900,
    "runtime_formatted": "5h 15m",
    "sessions": 4
  },
  "day_before": {
    "date": "2025-11-26",
    "runtime_seconds": 14400,
    "runtime_formatted": "4h 0m",
    "sessions": 3
  },
  "last_7_days": {
    "runtime_seconds": 116400,
    "runtime_formatted": "32h 20m",
    "sessions": 25,
    "average_per_day": "4h 37m"
  }
}
```

#### DAILY_SUMMARY
Save today's summary to file.

**Request**: `DAILY_SUMMARY`

**Response**:
```json
{
  "status": "success",
  "message": "Daily summary saved"
}
```

#### HISTORICAL
Get all historical summaries.

**Request**: `HISTORICAL`

**Response**:
```json
{
  "status": "success",
  "summaries": {
    "2025-11-28": {
      "runtime_seconds": 16200,
      "runtime_formatted": "4h 30m",
      "sessions": 3,
      "timestamp": "2025-11-28T23:55:00"
    },
    "2025-11-27": {
      "runtime_seconds": 18900,
      "runtime_formatted": "5h 15m",
      "sessions": 4,
      "timestamp": "2025-11-27T23:55:00"
    }
  }
}
```

### Example Usage

```python
import socket
import json

def request_summary(command="SUMMARY"):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(30)
    client.connect(('localhost', 9999))
    client.sendall(command.encode('utf-8'))
    response = client.recv(8192).decode('utf-8')
    client.close()
    return json.loads(response)

# Get summary
summary = request_summary("SUMMARY")
print(f"Today: {summary['today']['runtime_formatted']}")

# Get historical
historical = request_summary("HISTORICAL")
for date, data in historical['summaries'].items():
    print(f"{date}: {data['runtime_formatted']}")
```

## Arduino Serial Protocol

### From Raspberry Pi to Arduino

```
TIME:1732627800          # Set time (Unix timestamp)
OVERRIDE:ON              # Manual on
OVERRIDE:OFF             # Manual off
OVERRIDE:AUTO            # Auto mode
SCHED:0:6:0:8:30        # Update schedule
CLEAR_SCHED             # Clear schedules
STATUS                  # Request status
GET_SCHEDULES           # Request schedule list
```

### From Arduino to Raspberry Pi

```
READY                                    # Startup message
TIME_SYNC_REQUEST                        # Request time sync
TIME_SET:1732627800:06:00                # Time confirmed
STATUS:STARTED                           # Boiler started (AUTO)
STATUS:STOPPED                           # Boiler stopped (AUTO)
STATUS:STARTED_MANUAL                    # Started manually
STATUS:STOPPED_MANUAL                    # Stopped manually
MODE:AUTO                                # Mode changed
MODE:MANUAL_ON                           # Mode changed
MODE:MANUAL_OFF                          # Mode changed
HEARTBEAT:06:00:ON:AUTO                 # Regular heartbeat
SCHED_UPDATED:0:6:0-8:30                # Schedule confirmed
SCHEDULES_CLEARED                        # Schedules cleared
ERROR:message                           # Error occurred
```

## Error Handling

### Timeouts
All socket operations have timeouts:
- Command port: 5 seconds
- Notification port: 2 seconds
- Summary port: 30 seconds

### Connection Refused
If service not running, socket.connect() raises `ConnectionRefusedError`.

Handle gracefully:
```python
try:
    client.connect(('localhost', 5000))
except ConnectionRefusedError:
    print("Service not available")
    return None
```

### Malformed Responses
Always wrap JSON parsing in try/except:
```python
try:
    result = json.loads(response)
except json.JSONDecodeError:
    print("Invalid response format")
    return None
```

## Security

- **Local only**: All sockets bind to 127.0.0.1
- **No authentication**: Services trust localhost communication
- **Input validation**: Commands validated before execution
- **No encryption**: Not needed for localhost

## Performance

- **Latency**: < 10ms for local sockets
- **Throughput**: Not a bottleneck (low message rate)
- **Concurrency**: Services handle multiple connections via threading

## Extending the API

To add new commands:

1. Add handler in `handle_command_connection()` (smart_thermostat.py)
2. Document in this file
3. Update client code (telegram_controller.py)
4. Test with manual socket connection
5. Add to integration tests

