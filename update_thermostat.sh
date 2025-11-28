#!/bin/bash
#
# Smart Thermostat - Update Script
# =================================
#
# Updates thermostat software from Git repository and restarts services.
# Uses systemd service management for reliable operation.
#
# Author: Cem
# Version: 1.0.0
# License: MIT
#

VERSION="1.0.0"

echo "=================================================="
echo "Thermostat Update Script v${VERSION}"
echo "=================================================="

# Pull latest code from git
echo "Pulling latest code from git..."
cd ~/thermostat-repo
git pull origin main

if [ $? -ne 0 ]; then
    echo "✗ Git pull failed"
    exit 1
fi

# Copy updated files to home directory
echo "Copying updated files..."
cp smart_thermostat.py ~/smart_thermostat.py
cp telegram_controller.py ~/telegram_controller.py
cp summary.py ~/summary.py

# Copy .env file if it exists (important!)
if [ -f .env ]; then
    cp .env ~/.env
    echo "✓ Updated .env file"
fi

echo "✓ Files copied successfully"

# Restart systemd services
echo "Restarting services..."

# Stop services first
sudo systemctl stop smart-thermostat.service
sudo systemctl stop telegram-controller.service
sudo systemctl stop thermostat-summary.service

# Wait a moment
sleep 2

# Start services in order (smart-thermostat first, then telegram-controller)
echo "Starting smart-thermostat.service..."
sudo systemctl start smart-thermostat.service

# Wait for smart-thermostat to be ready
sleep 3

echo "Starting telegram-controller.service..."
sudo systemctl start telegram-controller.service

echo "Starting thermostat-summary.service..."
sudo systemctl start thermostat-summary.service

# Wait a moment for services to start
sleep 2

echo ""
echo "=================================================="
echo "Service Status:"
echo "=================================================="

# Check status of all services
sudo systemctl is-active smart-thermostat.service && echo "✓ smart-thermostat.service: RUNNING" || echo "✗ smart-thermostat.service: FAILED"
sudo systemctl is-active telegram-controller.service && echo "✓ telegram-controller.service: RUNNING" || echo "✗ telegram-controller.service: FAILED"
sudo systemctl is-active thermostat-summary.service && echo "✓ thermostat-summary.service: RUNNING" || echo "✗ thermostat-summary.service: FAILED"

echo ""
echo "=================================================="
echo "✓ Update Complete!"
echo "=================================================="
echo ""
echo "To view logs, use:"
echo "  sudo journalctl -u smart-thermostat.service -f"
echo "  sudo journalctl -u telegram-controller.service -f"
echo ""