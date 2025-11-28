# Emergency Fix for Restart Loop

## Bugs Fixed

### 1. Missing Import (telegram_controller.py)
- **Bug**: `BackgroundScheduler` was used but not imported
- **Fix**: Added `from apscheduler.schedulers.background import BackgroundScheduler`

### 2. Async Function Issue (telegram_controller.py)
- **Bug**: `send_daily_summary()` declared as `async` but contains no `await` calls
- **Fix**: Removed `async` keyword (it's now a regular function)

### 3. Duplicate Import (summary.py)
- **Bug**: `socket` imported twice
- **Fix**: Removed duplicate import

### 4. Better Error Handling (telegram_controller.py)
- **Added**: Comprehensive error logging with stack traces
- **Added**: Startup progress indicators [1/6] through [6/6]
- **Result**: If it crashes, you'll see EXACTLY where and why

## On Your Pi - Run These Commands

### Step 1: Stop the Loop
```bash
sudo systemctl stop telegram-controller.service
sudo systemctl stop smart-thermostat.service
```

### Step 2: Update Code
```bash
cd ~
./update_thermostat.sh
```

### Step 3: Run Diagnostic Test
```bash
cd ~/thermostat-repo
python3 test_telegram_bot.py
```

This will test:
- ✅ .env configuration
- ✅ Telegram bot connection
- ✅ Message sending
- ✅ All imports and dependencies

**If the diagnostic test fails**, it will tell you EXACTLY what's wrong.

### Step 4: Check systemd Logs for ACTUAL Error
```bash
# Watch telegram_controller startup in real-time
sudo journalctl -u telegram-controller.service -f
```

In another terminal:
```bash
# Start just telegram_controller
sudo systemctl start telegram-controller.service
```

**Look for** the startup progress messages:
```
[1/6] Starting notification server...
[2/6] Loading schedules...
[3/6] Waiting for smart_thermostat.py...
[4/6] Sending schedules to Arduino...
[5/6] Building Telegram application...
[6/6] Setting up scheduler...
✅ TELEGRAM CONTROLLER READY
```

**If it crashes**, you'll see:
```
❌ FATAL ERROR: <error message>
Error type: <error type>
<full stack trace>
```

**Send me this error output** and I'll know exactly what's wrong!

### Step 5: Manual Test (if diagnostic passed)
```bash
# Run telegram_controller manually (not as service)
cd ~
source ~/thermostat-env/bin/activate
python3 telegram_controller.py
```

Watch the output. If it runs past "Starting bot polling...", it's working!
Press Ctrl+C to stop, then start as service:

```bash
sudo systemctl start smart-thermostat.service
sleep 3
sudo systemctl start telegram-controller.service
```

## Common Issues & Solutions

### Issue: "Conflict: terminated by other getUpdates request"
**Cause**: Multiple telegram_controller instances running
**Fix**:
```bash
pkill -f telegram_controller
ps aux | grep telegram_controller  # verify none running
sudo systemctl start telegram-controller.service
```

### Issue: "Network is unreachable" / "Connection timeout"
**Cause**: No internet connection
**Fix**: Check Pi's network connection

### Issue: "Unauthorized" or "Invalid token"
**Cause**: Wrong TELEGRAM_BOT_TOKEN in .env
**Fix**:
1. Get new token from @BotFather
2. Update ~/.env
3. Restart service

### Issue: Port 5001 already in use
**Cause**: Old notification server still running
**Fix**:
```bash
sudo netstat -tlnp | grep 5001
# Kill the process shown
kill <PID>
```

## What I Need From You

Run the diagnostic test and send me:

1. **Diagnostic test output**:
   ```bash
   python3 ~/thermostat-repo/test_telegram_bot.py > ~/test_output.txt 2>&1
   cat ~/test_output.txt
   ```

2. **Telegram controller startup logs**:
   ```bash
   sudo journalctl -u telegram-controller.service -n 50 --no-pager > ~/startup_log.txt
   cat ~/startup_log.txt
   ```

3. **Process list**:
   ```bash
   ps aux | grep -E "telegram_controller|smart_thermostat" | grep -v grep
   ```

With these three outputs, I'll know EXACTLY what's causing the restart loop!

---

## Quick Summary

**What we fixed**:
- Missing import causing NameError
- Async function causing scheduler issues
- Added detailed error logging

**What you need to do**:
1. Stop services
2. Run update script
3. Run diagnostic test
4. Send me the outputs

This will 100% identify the problem!
