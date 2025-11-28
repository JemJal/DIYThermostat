#!/bin/bash
#
# Smart Thermostat - Update Script
# =================================
#
# Updates thermostat software from Git repository and restarts services.
# Uses systemd service management for reliable operation.
# FORCE PULL: Discards all local changes in repo and pulls fresh code.
#
# Author: Cem
# Version: 1.0.0
# License: MIT
#

VERSION="1.0.0"

set -e  # Exit on any error

echo "=========================================================="
echo "   Smart Thermostat Update Script v${VERSION}"
echo "=========================================================="
echo ""

# Check if running on Pi (basic check)
if [ ! -d "/home/cem" ]; then
    echo "⚠️  WARNING: This script is designed for Raspberry Pi"
    echo "   Not running in expected environment"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Navigate to repo directory
echo "📁 Navigating to repository..."
cd ~/thermostat-repo || {
    echo "✗ Error: ~/thermostat-repo directory not found"
    echo "  Please clone the repository first:"
    echo "  git clone https://github.com/yourusername/DIYThermostat.git ~/thermostat-repo"
    exit 1
}

# Backup .env file if it exists (in case it's in the repo by mistake)
echo "💾 Checking for .env backup..."
if [ -f .env ]; then
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    echo "✓ Backed up .env file in repo"
fi

# Force pull: Discard all local changes and pull fresh code
echo ""
echo "🔄 Force pulling latest code from Git..."
echo "   (This will discard any local changes in the repo)"

# Fetch latest from origin
git fetch origin main || {
    echo "✗ Error: Failed to fetch from origin"
    echo "  Check your internet connection and Git configuration"
    exit 1
}

# Reset hard to origin/main (discard all local changes)
git reset --hard origin/main || {
    echo "✗ Error: Failed to reset to origin/main"
    exit 1
}

# Clean untracked files
git clean -fd

echo "✓ Code updated successfully"
echo ""

# Copy updated files to home directory
echo "📋 Copying updated files to home directory..."

cp smart_thermostat.py ~/smart_thermostat.py || {
    echo "✗ Error: Failed to copy smart_thermostat.py"
    exit 1
}
echo "  ✓ smart_thermostat.py"

cp telegram_controller.py ~/telegram_controller.py || {
    echo "✗ Error: Failed to copy telegram_controller.py"
    exit 1
}
echo "  ✓ telegram_controller.py"

cp summary.py ~/summary.py || {
    echo "✗ Error: Failed to copy summary.py"
    exit 1
}
echo "  ✓ summary.py"

# Check if .env exists in repo (it shouldn't, but just in case)
if [ -f .env ]; then
    echo "  ⚠️  .env found in repo (copying to home)"
    cp .env ~/.env
    echo "  ✓ .env file"
fi

echo ""

# Check if .env file exists in home directory
echo "🔧 Checking configuration..."
if [ ! -f ~/.env ]; then
    echo ""
    echo "⚠️  WARNING: ~/.env file not found!"
    echo ""
    echo "   The system requires a .env file with your configuration."
    echo "   Please create it before the services can start properly."
    echo ""
    echo "   Steps:"
    echo "   1. cp ~/thermostat-repo/.env.example ~/.env"
    echo "   2. nano ~/.env  (edit with your settings)"
    echo "   3. Run this script again"
    echo ""
    read -p "Continue anyway? Services will likely fail. (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Exiting. Please create ~/.env and run again."
        exit 1
    fi
else
    echo "✓ Configuration file found (~/.env)"
fi

# Check if schedule file exists
if [ ! -f ~/schedule.json ]; then
    echo "⚠️  Warning: ~/schedule.json not found"
    echo "   Creating from example..."
    if [ -f ~/thermostat-repo/schedule.json.example ]; then
        cp ~/thermostat-repo/schedule.json.example ~/schedule.json
        echo "✓ Created ~/schedule.json from example"
    else
        echo "⚠️  Could not create schedule.json (example not found)"
    fi
else
    echo "✓ Schedule file found (~/schedule.json)"
fi

echo ""

# Restart systemd services
echo "🔄 Restarting services..."
echo ""

# Stop all services
echo "  Stopping services..."
sudo systemctl stop smart-thermostat.service 2>/dev/null || true
sudo systemctl stop telegram-controller.service 2>/dev/null || true
sudo systemctl stop thermostat-summary.service 2>/dev/null || true

# Wait for clean shutdown
sleep 2

# Start services in correct order
echo "  Starting smart-thermostat.service..."
sudo systemctl start smart-thermostat.service || {
    echo "  ✗ Failed to start smart-thermostat.service"
    echo "  Check: sudo journalctl -u smart-thermostat.service -n 20"
    exit 1
}

# Wait for smart-thermostat to initialize
sleep 3

echo "  Starting telegram-controller.service..."
sudo systemctl start telegram-controller.service || {
    echo "  ✗ Failed to start telegram-controller.service"
    echo "  Check: sudo journalctl -u telegram-controller.service -n 20"
    exit 1
}

echo "  Starting thermostat-summary.service..."
sudo systemctl start thermostat-summary.service || {
    echo "  ✗ Failed to start thermostat-summary.service"
    echo "  Check: sudo journalctl -u thermostat-summary.service -n 20"
    exit 1
}

# Wait for services to fully start
sleep 3

echo ""
echo "=========================================================="
echo "   Service Status Check"
echo "=========================================================="
echo ""

# Check status of all services with detailed feedback
SMART_STATUS=$(sudo systemctl is-active smart-thermostat.service)
TELEGRAM_STATUS=$(sudo systemctl is-active telegram-controller.service)
SUMMARY_STATUS=$(sudo systemctl is-active thermostat-summary.service)

if [ "$SMART_STATUS" = "active" ]; then
    echo "✓ smart-thermostat.service:    RUNNING"
else
    echo "✗ smart-thermostat.service:    FAILED ($SMART_STATUS)"
fi

if [ "$TELEGRAM_STATUS" = "active" ]; then
    echo "✓ telegram-controller.service: RUNNING"
else
    echo "✗ telegram-controller.service: FAILED ($TELEGRAM_STATUS)"
fi

if [ "$SUMMARY_STATUS" = "active" ]; then
    echo "✓ thermostat-summary.service:  RUNNING"
else
    echo "✗ thermostat-summary.service:  FAILED ($SUMMARY_STATUS)"
fi

echo ""

# Final status message
if [ "$SMART_STATUS" = "active" ] && [ "$TELEGRAM_STATUS" = "active" ] && [ "$SUMMARY_STATUS" = "active" ]; then
    echo "=========================================================="
    echo "   ✨ Update Complete! All Systems Running! ✨"
    echo "=========================================================="
    echo ""
    echo "Your thermostat is now updated and running."
    echo ""
    echo "Quick checks:"
    echo "  • Send /status to your Telegram bot"
    echo "  • Check logs: sudo journalctl -u smart-thermostat.service -n 20"
    echo ""
    echo "Everything should work like magic! 🪄"
else
    echo "=========================================================="
    echo "   ⚠️  Update Complete but Some Services Failed"
    echo "=========================================================="
    echo ""
    echo "Please check the logs for errors:"
    echo ""
    if [ "$SMART_STATUS" != "active" ]; then
        echo "  sudo journalctl -u smart-thermostat.service -n 50"
    fi
    if [ "$TELEGRAM_STATUS" != "active" ]; then
        echo "  sudo journalctl -u telegram-controller.service -n 50"
    fi
    if [ "$SUMMARY_STATUS" != "active" ]; then
        echo "  sudo journalctl -u thermostat-summary.service -n 50"
    fi
    echo ""
    echo "Common issues:"
    echo "  • Missing or incorrect ~/.env file"
    echo "  • Wrong Arduino port in ~/.env"
    echo "  • Missing Python dependencies"
    echo ""
    exit 1
fi

echo ""