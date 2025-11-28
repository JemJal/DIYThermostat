#!/usr/bin/env python3
"""
Diagnostic script to test Telegram bot configuration
Run this on the Pi to identify issues before starting the full service
"""

import sys
import os
from dotenv import load_dotenv

print("=" * 60)
print("Telegram Bot Configuration Test")
print("=" * 60)
print()

# Load .env
print("[1/6] Loading .env file...")
load_dotenv(os.path.expanduser('~/.env'))
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

if not TELEGRAM_BOT_TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN is missing from .env")
    sys.exit(1)
if not TELEGRAM_CHAT_ID:
    print("❌ TELEGRAM_CHAT_ID is missing from .env")
    sys.exit(1)

print(f"✓ TELEGRAM_BOT_TOKEN: {TELEGRAM_BOT_TOKEN[:10]}...{TELEGRAM_BOT_TOKEN[-5:]}")
print(f"✓ TELEGRAM_CHAT_ID: {TELEGRAM_CHAT_ID}")
print()

# Test imports
print("[2/6] Testing imports...")
try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, ContextTypes
    print("✓ python-telegram-bot imports successful")
    import telegram
    print(f"✓ python-telegram-bot version: {telegram.__version__}")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("   Run: pip install python-telegram-bot==20.7")
    sys.exit(1)
print()

# Test bot connection
print("[3/6] Testing bot connection...")
try:
    import requests
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"
    response = requests.get(url, timeout=10)
    if response.status_code == 200:
        data = response.json()
        if data.get('ok'):
            bot_info = data.get('result', {})
            print(f"✓ Bot connected successfully")
            print(f"  Bot name: {bot_info.get('first_name')}")
            print(f"  Bot username: @{bot_info.get('username')}")
        else:
            print(f"❌ Bot API returned error: {data}")
            sys.exit(1)
    else:
        print(f"❌ HTTP error {response.status_code}")
        sys.exit(1)
except requests.exceptions.Timeout:
    print("❌ Connection timeout - check internet connectivity")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
print()

# Test sending a message
print("[4/6] Testing message send...")
try:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": "🧪 Test message from diagnostic script",
    }
    response = requests.post(url, json=payload, timeout=10)
    if response.status_code == 200:
        print("✓ Test message sent successfully")
        print("  Check your Telegram to confirm you received it")
    else:
        print(f"❌ Failed to send message: {response.status_code}")
        print(f"  Response: {response.text}")
        print("  Check if TELEGRAM_CHAT_ID is correct")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error sending message: {e}")
    sys.exit(1)
print()

# Test Application builder
print("[5/6] Testing Application builder...")
try:
    from telegram.ext import Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    print("✓ Application built successfully")
except Exception as e:
    print(f"❌ Failed to build application: {e}")
    sys.exit(1)
print()

# Test scheduler
print("[6/6] Testing APScheduler...")
try:
    from apscheduler.schedulers.background import BackgroundScheduler

    def test_job():
        print("  Test job executed")

    scheduler = BackgroundScheduler()
    scheduler.add_job(test_job, 'date', run_date='2099-01-01 00:00:00')
    print("✓ Scheduler setup successful")
except Exception as e:
    print(f"❌ Scheduler error: {e}")
    sys.exit(1)
print()

print("=" * 60)
print("✅ ALL TESTS PASSED")
print("=" * 60)
print()
print("Your configuration looks good!")
print("If telegram_controller still crashes, check:")
print("1. Systemd logs: sudo journalctl -u telegram-controller.service -n 100")
print("2. Port conflicts: sudo netstat -tlnp | grep -E '5000|5001'")
print("3. Firewall settings")
print()
