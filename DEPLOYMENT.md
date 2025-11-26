# Deployment Instructions

## What Was Fixed

### Critical Issues Resolved:
1. **Serial Port Conflict** - Both `smart_thermostat.py` and `telegram_controller.py` were trying to access Arduino simultaneously, causing corrupted messages
2. **Duplicate Processes** - Screen sessions and systemd services were running simultaneously
3. **Architecture Flaw** - No coordination between the two main scripts

### New Architecture:
```
Telegram Bot → telegram_controller.py → [Socket Port 5000] → smart_thermostat.py → Arduino
```

- **smart_thermostat.py**: Only process that communicates with Arduino via serial
- **telegram_controller.py**: Sends commands via socket to smart_thermostat.py
- No more serial port conflicts!

---

## Deployment Steps

### Step 1: Clean Up Old Processes

SSH to your Raspberry Pi and run:

```bash
# Stop all running services
sudo systemctl stop smart-thermostat.service
sudo systemctl stop telegram-controller.service
sudo systemctl stop thermostat-summary.service

# Kill any screen sessions
screen -ls | grep -E 'thermostat|telegram|summary' | cut -d. -f1 | awk '{print $1}' | xargs -I {} screen -X -S {} quit

# Kill any remaining Python processes
pkill -f "python3.*smart_thermostat"
pkill -f "python3.*telegram_controller"
pkill -f "python3.*summary"

# Verify nothing is running
ps aux | grep -E "smart_thermostat|telegram_controller|summary" | grep -v grep
# Should return nothing
```

### Step 2: Push Code to Git

On your local machine:

```bash
cd /Users/cem/Projects/DIYThermostat

# Add all changes
git add .

# Commit
git commit -m "Fix serial port conflict and refactor architecture"

# Push to main
git push origin main
```

### Step 3: Update Services on Pi

SSH to your Pi:

```bash
# Navigate to repo directory
cd ~/thermostat-repo

# Pull latest code
git pull origin main

# Make update script executable
chmod +x update_thermostat.sh

# Copy .env file to home directory (IMPORTANT!)
cp .env ~/.env

# Verify .env was copied
cat ~/.env
```

### Step 4: Update Systemd Service Files

The telegram-controller.service needs updating to ensure it waits for smart-thermostat:

```bash
sudo nano /etc/systemd/system/telegram-controller.service
```

Make sure it has these lines in the `[Unit]` section:
```ini
After=network.target smart-thermostat.service
Requires=smart-thermostat.service
```

Save and reload:
```bash
sudo systemctl daemon-reload
```

### Step 5: Run the Update Script

```bash
cd ~
./update_thermostat.sh
```

You should see:
```
✓ smart-thermostat.service: RUNNING
✓ telegram-controller.service: RUNNING
✓ thermostat-summary.service: RUNNING
```

### Step 6: Verify Clean Communication

Watch the logs for clean messages (no corruption):

```bash
# In one terminal:
sudo journalctl -u smart-thermostat.service -f

# Look for:
# - "✓ Command server listening on port 5000"
# - "✓ Connected to Arduino on /dev/serial..."
# - "✓ Time synced to Arduino"
# - Clean "HEARTBEAT:HH:MM:ON/OFF:AUTO" messages (not garbled)
```

```bash
# In another terminal:
sudo journalctl -u telegram-controller.service -f

# Look for:
# - "✓ Command sent: CLEAR_SCHED"
# - "✓ Command sent: SCHED:0:6:0:8:0"
# - "✓ Sent N schedules to Arduino"
# - "✓ Telegram bot started"
```

### Step 7: Test via Telegram

Send these commands and verify they work:

1. `/status` - Should show current status with clean data
2. `/schedule` - Should show your schedules
3. `/auto` - Switch to auto mode
4. `/debug` - Verify mode is AUTO

### Step 8: Test Automatic Control

Edit your schedule to start in 2-3 minutes from now:

```bash
nano ~/schedule.json
```

Example (if it's 14:30, set schedule for 14:32-14:35):
```json
{
  "schedules": [
    {
      "name": "Test",
      "startHour": 14,
      "startMinute": 32,
      "endHour": 14,
      "endMinute": 35
    }
  ]
}
```

Then:
```bash
# Restart telegram-controller to load new schedule
sudo systemctl restart telegram-controller.service

# Watch logs
sudo journalctl -u smart-thermostat.service -f

# At 14:32, you should see:
# "Arduino: STATUS:STARTED"
```

---

## Verification Checklist

After deployment, verify:

- [ ] Only ONE instance of each service running
- [ ] No "multiple access on port" errors
- [ ] No garbled messages (ATBAT0:F:UTO)
- [ ] No Telegram conflicts
- [ ] Heartbeat messages are clean: `HEARTBEAT:HH:MM:ON/OFF:AUTO`
- [ ] Schedules sent successfully on startup
- [ ] `/on`, `/off`, `/auto` commands work
- [ ] `/status` shows correct mode
- [ ] Boiler activates automatically at scheduled time

---

## Troubleshooting

### If services fail to start:

```bash
# Check detailed error messages
sudo journalctl -u smart-thermostat.service -n 50 --no-pager
sudo journalctl -u telegram-controller.service -n 50 --no-pager

# Check if .env file exists
ls -la ~/.env

# Check if Arduino is connected
ls -la /dev/serial/by-id/

# Restart services manually
sudo systemctl restart smart-thermostat.service
sleep 3
sudo systemctl restart telegram-controller.service
```

### If you see "Connection refused" in telegram-controller logs:

This means `smart_thermostat.py` isn't running or the socket server didn't start.

```bash
# Make sure smart-thermostat is running
sudo systemctl status smart-thermostat.service

# Check if port 5000 is listening
sudo netstat -tlnp | grep 5000
# Should show python3 listening on 127.0.0.1:5000
```

### To manually test socket communication:

```bash
# Test sending a command
echo "GET_STATUS" | nc localhost 5000
# Should return JSON response
```

---

## Rolling Back (if needed)

If something goes wrong:

```bash
cd ~/thermostat-repo
git checkout HEAD~1  # Go back to previous version
./update_thermostat.sh
```

---

## Success Indicators

You'll know it's working when:

1. ✅ Logs show clean, readable messages
2. ✅ No "multiple access" or "conflict" errors
3. ✅ Heartbeats appear every 30 seconds with correct time
4. ✅ Telegram commands respond instantly
5. ✅ **Boiler turns on/off automatically at scheduled times**

---

## Notes

- The `.env` file MUST exist at `~/.env` on the Pi
- `smart_thermostat.py` MUST start before `telegram_controller.py`
- Only `smart_thermostat.py` communicates with Arduino (via serial)
- Only `telegram_controller.py` communicates with Telegram
- They communicate with each other via local socket (port 5000)
