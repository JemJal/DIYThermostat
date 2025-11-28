# AUTO Mode Notification Feature

## Clean Architecture Implementation

As requested, I've implemented the notification feature with **complete separation of concerns**:

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Arduino UNO                          │
│                   (Thermostat Control)                      │
└──────────────────────────┬──────────────────────────────────┘
                           │ Serial Port
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                   smart_thermostat.py                       │
│  - Reads Arduino messages                                   │
│  - Syncs time                                               │
│  - Monitors heartbeat                                       │
│  - Socket server on port 5000 (receives commands)           │
│  - Socket client to port 5001 (sends notification requests) │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           │ Notification Requests (Port 5001)
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                 telegram_controller.py                      │
│  - Socket server on port 5001 (receives notification reqs)  │
│  - Sends Telegram messages                                  │
│  - Telegram bot commands                                    │
│  - Socket client to port 5000 (sends commands)              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           │ Telegram API
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                      Telegram Bot                           │
│                     (User Interface)                        │
└─────────────────────────────────────────────────────────────┘
```

### Communication Flow

**Two-way socket communication:**

1. **Command Flow** (Port 5000):
   ```
   User → Telegram → telegram_controller.py → [Socket 5000] → smart_thermostat.py → Arduino
   ```

2. **Notification Flow** (Port 5001):
   ```
   Arduino → smart_thermostat.py → [Socket 5001] → telegram_controller.py → Telegram → User
   ```

---

## How It Works

### When Boiler Starts (AUTO mode):

1. ⏰ **Schedule time arrives** (e.g., 06:00)
2. 🤖 **Arduino** detects it's time to start, activates relays
3. 📤 **Arduino** sends: `STATUS:STARTED` via serial
4. 📥 **smart_thermostat.py** receives the message
5. 🔌 **smart_thermostat.py** sends notification request to port 5001:
   ```json
   {
     "type": "notification",
     "message": "🔥 Boiler Started\n\n⏰ Time: 06:00\n🔄 Mode: AUTO"
   }
   ```
6. 📥 **telegram_controller.py** receives the request on port 5001
7. 📱 **telegram_controller.py** sends Telegram message to you
8. ✅ **You receive notification** on your phone!

### When Boiler Stops (AUTO mode):

Same flow, but with `STATUS:STOPPED` and "❄️ Boiler Stopped" message.

### Manual Mode:

- When you send `/on` or `/off`, **no notification** is sent
- You already know about manual commands, so no need for notifications
- Only AUTO mode (schedule-based) triggers notifications

---

## Separation of Concerns

### smart_thermostat.py
**Responsibilities:**
- ✅ Arduino serial communication
- ✅ Time synchronization
- ✅ Heartbeat monitoring
- ✅ Command execution (receives from telegram_controller)
- ✅ Notification requests (sends to telegram_controller)

**Does NOT:**
- ❌ Send Telegram messages directly
- ❌ Know about Telegram API
- ❌ Handle user commands

### telegram_controller.py
**Responsibilities:**
- ✅ Telegram bot communication
- ✅ User command handling (/on, /off, /auto, etc.)
- ✅ Schedule management
- ✅ Sending notifications
- ✅ Command forwarding (sends to smart_thermostat)

**Does NOT:**
- ❌ Communicate with Arduino directly
- ❌ Access serial port
- ❌ Know about Arduino protocol

---

## Files Modified

### smart_thermostat.py
**Changes:**
- Added `NOTIFICATION_PORT = 5001` configuration
- Added `request_notification(message)` function
- Sends notification requests when `STATUS:STARTED` or `STATUS:STOPPED` received
- Uses socket client to communicate with telegram_controller

**Removed:**
- ❌ No Telegram imports
- ❌ No Telegram API calls
- ❌ No direct message sending

### telegram_controller.py
**Changes:**
- Added `NOTIFICATION_PORT = 5001` configuration
- Added `send_telegram_message(message)` function
- Added `handle_notification_request()` function
- Added `notification_server()` - socket server on port 5001
- Started notification server thread in main

---

## What You'll Receive

### Boiler Starts Automatically:
```
🔥 Boiler Started

⏰ Time: 06:00
🔄 Mode: AUTO
```

### Boiler Stops Automatically:
```
❄️ Boiler Stopped

⏰ Time: 08:00
🔄 Mode: AUTO
```

**Note:** No notifications for manual `/on` or `/off` commands!

---

## Deployment

### Step 1: Push to Git
```bash
cd /Users/cem/Projects/DIYThermostat
git add .
git commit -m "Add AUTO mode notifications with clean architecture"
git push origin main
```

### Step 2: Deploy to Raspberry Pi
```bash
# SSH to your Pi
cd ~
./update_thermostat.sh
```

### Step 3: Verify
```bash
# Check both services started successfully
sudo systemctl status smart-thermostat.service
sudo systemctl status telegram-controller.service

# Check logs for notification server
sudo journalctl -u telegram-controller.service | grep "Notification server listening"
# Should show: "✓ Notification server listening on port 5001"
```

### Step 4: Test
Set a schedule for 2 minutes from now and verify you receive notification!

---

## Testing the Feature

### Quick Test:

1. **Edit schedule** to start in 2 minutes:
   ```bash
   nano ~/schedule.json
   ```

2. **Restart telegram-controller** to load new schedule:
   ```bash
   sudo systemctl restart telegram-controller.service
   ```

3. **Send** `/auto` command to ensure AUTO mode

4. **Wait** for scheduled time

5. **Receive notification!** 📱

---

## Architecture Benefits

### Clean Separation:
- ✅ Each file has a single, clear responsibility
- ✅ Easy to test independently
- ✅ Easy to modify without affecting other parts
- ✅ No circular dependencies

### Scalability:
- ✅ Can add more notification types easily
- ✅ Can replace Telegram with another service without changing smart_thermostat.py
- ✅ Can add multiple notification receivers

### Reliability:
- ✅ If telegram_controller crashes, smart_thermostat continues working
- ✅ Notification failure doesn't affect Arduino control
- ✅ Graceful degradation

---

## Troubleshooting

### If notifications don't arrive:

1. **Check notification server is running:**
   ```bash
   sudo netstat -tlnp | grep 5001
   # Should show python3 listening on 127.0.0.1:5001
   ```

2. **Check logs for notification requests:**
   ```bash
   sudo journalctl -u smart-thermostat.service -f
   # Should see: "✓ Notification request sent: 🔥 Boiler Started..."
   ```

3. **Check telegram-controller received it:**
   ```bash
   sudo journalctl -u telegram-controller.service -f
   # Should see: "✓ Telegram message sent: 🔥 Boiler Started..."
   ```

4. **Verify Telegram credentials:**
   ```bash
   cat ~/.env | grep TELEGRAM
   # Should show valid BOT_TOKEN and CHAT_ID
   ```

---

## Success!

Your thermostat now has **clean, separated notification functionality**:
- 🔥 Get notified when boiler starts automatically
- ❄️ Get notified when boiler stops automatically
- 🏗️ Maintain clean architecture
- 🔧 Easy to maintain and extend

Enjoy your automated notifications! 🎉
