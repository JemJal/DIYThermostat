# Quick Setup for Raspberry Pi

## Fresh Pi Setup (After Pushing V1.0)

After you push V1.0 to GitHub and want to set up your Pi "like magic":

### 1. SSH to Your Pi

```bash
ssh cem@your-pi-ip
```

### 2. Setup .env File (One Time Only)

The update script will warn you if this is missing, but it's better to do it first:

```bash
# Copy the example
cp ~/thermostat-repo/.env.example ~/.env

# Edit with your actual settings
nano ~/.env
```

**Required settings:**
- `TELEGRAM_BOT_TOKEN` - Your bot token from @BotFather
- `TELEGRAM_CHAT_ID` - Your Telegram chat ID
- `ARDUINO_PORT` - Your Arduino serial port (see below)
- `LOG_FILE` - `/home/cem/smart_thermostat.log`
- `SCHEDULE_FILE` - `/home/cem/schedule.json`

**Find your Arduino port:**
```bash
ls -la /dev/serial/by-id/
# Copy the full path, like:
# /dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A50285BI-if00-port0
```

Save and exit (`Ctrl+X`, `Y`, `Enter`)

### 3. Run the Magic Update Script

```bash
cd ~
./update_thermostat.sh
```

The script will:
- ✅ Force pull latest code (discards any local changes)
- ✅ Copy all Python files
- ✅ Check for .env file (warn if missing)
- ✅ Create schedule.json if missing
- ✅ Restart all services in correct order
- ✅ Check that everything is running
- ✅ Display success or helpful error messages

### 4. Test via Telegram

Send to your bot:
```
/status
```

Should show current status and mode!

---

## If You Get Merge Conflicts

If git pull complains about merge conflicts or uncommitted changes:

**Don't worry!** The new update script does a **FORCE PULL** which means:
- Discards ALL local changes in `~/thermostat-repo`
- Pulls fresh code from GitHub
- No merge conflicts possible

Just run:
```bash
./update_thermostat.sh
```

And it will handle everything automatically.

---

## After First Successful Setup

Every future update is just:

```bash
cd ~
./update_thermostat.sh
```

That's it! ✨

The script will:
1. Force pull latest code
2. Copy files
3. Restart services
4. Verify everything is running
5. Show you status

---

## Troubleshooting

### Script says ".env not found"

```bash
# Make sure it's in your home directory
ls -la ~/.env

# If missing, create it:
cp ~/thermostat-repo/.env.example ~/.env
nano ~/.env
# Fill in your settings, then run update script again
```

### Services fail to start

```bash
# Check the logs
sudo journalctl -u smart-thermostat.service -n 50
sudo journalctl -u telegram-controller.service -n 50

# Common issues:
# - Wrong ARDUINO_PORT in ~/.env
# - Missing Python dependencies (pip install -r requirements.txt)
# - Arduino not connected
```

### Need to start fresh?

```bash
# Stop everything
sudo systemctl stop smart-thermostat.service telegram-controller.service thermostat-summary.service

# Clean repo
cd ~/thermostat-repo
git fetch origin
git reset --hard origin/main
git clean -fd

# Run update script
cd ~
./update_thermostat.sh
```

---

## What the Script Does

### Force Pull Explained

Instead of:
```bash
git pull  # Can fail with conflicts
```

The script does:
```bash
git fetch origin main     # Download latest
git reset --hard origin/main  # Force local to match remote
git clean -fd            # Remove untracked files
```

This **guarantees** a clean pull every time, no conflicts possible.

### File Flow

```
GitHub → ~/thermostat-repo → ~/[files] → Services
```

1. Code pulled to `~/thermostat-repo` (your repo clone)
2. Files copied to `~/` (where services run from)
3. Services restarted to use new code

### Safety

- Your `.env` file is NEVER overwritten (it's in `~/`, not in repo)
- Your `schedule.json` is preserved
- Old .env backups created if found in repo (shouldn't be there)

---

## First Time After V1.0 Release

1. **On your Mac** (push the V1.0 code):
   ```bash
   git add .
   git commit -m "Release v1.0.0"
   git push origin main
   ```

2. **On your Pi** (pull and setup):
   ```bash
   # Ensure .env is configured
   nano ~/.env

   # Run the magic script
   ./update_thermostat.sh
   ```

3. **Test**:
   - Send `/status` to Telegram bot
   - Check it responds correctly
   - Done! 🎉

---

**Everything will work like magic!** 🪄

The script is designed to be foolproof:
- Clear error messages
- Automatic checks
- Helpful hints
- Force pull prevents conflicts
- Service status validation
- Success confirmation

Just fix your `.env` file once, then run the script whenever you update!
