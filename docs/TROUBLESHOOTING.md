# Troubleshooting Guide

Solutions to common problems with the Smart Thermostat System v1.0.0

## Quick Diagnostics

```bash
# Check service status
sudo systemctl status smart-thermostat.service
sudo systemctl status telegram-controller.service

# View recent logs
sudo journalctl -u smart-thermostat.service -n 50
sudo journalctl -u telegram-controller.service -n 50

# Check if Arduino connected
ls -la /dev/serial/by-id/

# Check if ports are listening
sudo netstat -tlnp | grep -E '5000|5001|9999'

# Verify .env file exists
cat ~/.env
```

## Common Issues

### 1. Services Won't Start

**Symptom**: `systemctl status` shows failed or inactive

**Causes & Solutions**:

**Missing .env file**:
```bash
# Check if file exists
ls -la ~/.env

# If missing, copy and configure
cp ~/thermostat-repo/.env.example ~/.env
nano ~/.env
```

**Wrong paths in .env**:
```bash
# Verify paths match your setup
cat ~/.env | grep -E 'PORT|FILE'

# Update if needed
nano ~/.env
```

**Python dependencies missing**:
```bash
source ~/thermostat-env/bin/activate
pip install -r ~/thermostat-repo/requirements.txt
```

**Permissions issues**:
```bash
# Check file ownership
ls -la ~/smart_thermostat.py

# Fix if needed
sudo chown youruser:youruser ~/smart_thermostat.py
```

### 2. Arduino Not Detected

**Symptom**: "Failed to connect to Arduino" in logs

**Solutions**:

**Find correct port**:
```bash
# List all serial devices
ls -la /dev/serial/by-id/

# Or try
dmesg | grep tty

# Update ARDUINO_PORT in ~/.env
```

**USB connection loose**:
- Check physical USB connection
- Try different USB port
- Check USB cable quality

**Permissions**:
```bash
# Add user to dialout group
sudo usermod -a -G dialout youruser

# Logout and login for changes to take effect
```

**Arduino not responding**:
- Re-upload Arduino sketch
- Check Arduino power LED
- Try resetting Arduino (button)

### 3. Schedules Not Working

**Symptom**: Boiler doesn't turn on at scheduled time

**Check these**:

**Is system in AUTO mode?**:
```
# Send via Telegram
/status

# Should show "Mode: AUTO"
# If not, send:
/auto
```

**Are schedules loaded?**:
```
# Check via Telegram
/schedule

# Should show your schedules
```

**Is time synchronized?**:
```bash
# Check logs for time sync
sudo journalctl -u smart-thermostat.service | grep "Time synced"

# Should see recent sync messages
```

**Is Arduino time correct?**:
```bash
# Check heartbeat in logs
sudo journalctl -u smart-thermostat.service | grep HEARTBEAT | tail -5

# Compare Arduino time with actual time
date "+%H:%M"
```

**Schedule file correct?**:
```bash
# View schedule
cat ~/schedule.json

# Verify format
# Times should be in 24-hour format
```

### 4. No Telegram Notifications

**Symptom**: Manual commands work but no AUTO notifications

**Check**:

**Notification server running?**:
```bash
# Check if port 5001 listening
sudo netstat -tlnp | grep 5001

# Should show python3 listening
```

**Logs show notification attempts?**:
```bash
# Check smart-thermostat logs
sudo journalctl -u smart-thermostat.service | grep "Notification request"

# Check telegram-controller logs
sudo journalctl -u telegram-controller.service | grep "Telegram message"
```

**Services started in correct order?**:
```bash
# smart-thermostat MUST start before telegram-controller
sudo systemctl restart smart-thermostat.service
sleep 3
sudo systemctl restart telegram-controller.service
```

### 5. Corrupted Arduino Messages

**Symptom**: Logs show garbled messages like "ATBAT0:F:UTO"

**Cause**: Multiple processes accessing serial port

**Solution**:
```bash
# Check for duplicate processes
ps aux | grep -E "smart_thermostat|telegram_controller" | grep -v grep

# Should see exactly 2 processes (one for each service)

# If more, stop all and restart properly
sudo systemctl stop smart-thermostat.service telegram-controller.service
pkill -f smart_thermostat
pkill -f telegram_controller
sleep 2
sudo systemctl start smart-thermostat.service
sleep 3
sudo systemctl start telegram-controller.service
```

### 6. Telegram Bot Conflicts

**Symptom**: "terminated by other getUpdates request"

**Cause**: Multiple telegram_controller instances running

**Solution**:
```bash
# Stop all instances
sudo systemctl stop telegram-controller.service
pkill -f telegram_controller

# Verify stopped
ps aux | grep telegram_controller | grep -v grep

# Start single instance
sudo systemctl start telegram-controller.service
```

### 7. Services Keep Restarting

**Symptom**: Services show restart loop in `systemctl status`

**Check logs for errors**:
```bash
sudo journalctl -u smart-thermostat.service -n 100

# Look for:
# - Missing configuration
# - Import errors
# - Port conflicts
```

**Common fixes**:
```bash
# Reinstall dependencies
source ~/thermostat-env/bin/activate
pip install --upgrade -r ~/thermostat-repo/requirements.txt

# Verify Python version
python3 --version  # Should be 3.9+

# Check file syntax
python3 -m py_compile ~/smart_thermostat.py
```

### 8. No Heartbeat Messages

**Symptom**: Logs show "No heartbeat for X seconds"

**Causes**:
1. Arduino not running (check power LED)
2. Serial connection broken (check USB)
3. Arduino code not uploaded
4. Time not synchronized (Arduino waiting)

**Solutions**:
```bash
# Check Arduino connection
ls -la /dev/serial/by-id/

# Restart services
sudo systemctl restart smart-thermostat.service

# Watch for READY message
sudo journalctl -u smart-thermostat.service -f

# Should see:
# - "Connected to Arduino"
# - "Time synced"
# - "HEARTBEAT:HH:MM:OFF:AUTO"
```

### 9. Wrong Timezone/Time

**Symptom**: Arduino reports wrong time, schedules off by hours

**Check**:
```bash
# Pi timezone
timedatectl

# Should match your location
# If not:
sudo timedatectl set-timezone Europe/Istanbul
```

**Arduino timezone**:
- Arduino code has UTC+3 offset for Turkey
- If different location, edit `arduino_thermostat.ino`:
  ```cpp
  const int TIMEZONE_OFFSET = 3 * 3600; // Change 3 to your offset
  ```

### 10. Summary Service Not Working

**Symptom**: `/summary` command shows error

**Check**:
```bash
# Is summary service running?
sudo systemctl status thermostat-summary.service

# Check if port 9999 listening
sudo netstat -tlnp | grep 9999

# View logs
sudo journalctl -u thermostat-summary.service -n 50
```

**Restart**:
```bash
sudo systemctl restart thermostat-summary.service
```

## Advanced Debugging

### Enable Debug Logging

Edit service file:
```bash
sudo nano /etc/systemd/system/smart-thermostat.service
```

Change `level=logging.INFO` to `level=logging.DEBUG` in the Python file:
```bash
nano ~/smart_thermostat.py
# Find: level=logging.INFO
# Change to: level=logging.DEBUG
```

Restart:
```bash
sudo systemctl restart smart-thermostat.service
```

### Test Socket Communication

**Test command port**:
```bash
echo "GET_STATUS" | nc localhost 5000
# Should return JSON response
```

**Test notification port**:
```bash
echo '{"type":"notification","message":"test"}' | nc localhost 5001
# Should return success
```

### Monitor Real-Time

```bash
# Watch all logs simultaneously
sudo journalctl -u smart-thermostat.service -u telegram-controller.service -f
```

### Check Python Environment

```bash
source ~/thermostat-env/bin/activate
pip list

# Verify all required packages installed:
# pyserial, python-telegram-bot, python-dotenv, requests, APScheduler
```

## Getting Help

If issues persist:

1. **Collect information**:
   ```bash
   # Save logs
   sudo journalctl -u smart-thermostat.service -n 200 > ~/debug-smart.log
   sudo journalctl -u telegram-controller.service -n 200 > ~/debug-telegram.log

   # System info
   uname -a > ~/debug-system.log
   python3 --version >> ~/debug-system.log
   cat ~/.env >> ~/debug-config.log  # Remove sensitive data first!
   ```

2. **Create GitHub issue** with:
   - Problem description
   - Steps to reproduce
   - Log excerpts (sanitized)
   - System configuration

3. **Check existing issues**: 
   https://github.com/yourusername/DIYThermostat/issues

## Prevention

### Regular Maintenance

```bash
# Weekly
sudo journalctl --vacuum-time=7d  # Clean old logs

# Monthly
sudo apt update && sudo apt upgrade
source ~/thermostat-env/bin/activate
pip list --outdated

# Check service health
sudo systemctl status smart-thermostat.service telegram-controller.service
```

### Backup

```bash
# Backup configuration
cp ~/.env ~/.env.backup
cp ~/schedule.json ~/schedule.json.backup

# Backup logs (monthly)
cp ~/smart_thermostat.log ~/logs/smart_thermostat-$(date +%Y%m).log
```

