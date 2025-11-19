#!/usr/bin/env python3
# Smart Thermostat - Arduino Manager
# Handles time sync, schedule management, and Arduino communication
# Telegram notifications are handled by telegram_controller.py

import serial
import time
import os
from datetime import datetime
from zoneinfo import ZoneInfo
import logging
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.expanduser('~/.env'))

# Configuration from .env
ARDUINO_PORT = os.getenv('ARDUINO_PORT')
BAUD_RATE = int(os.getenv('BAUD_RATE', 9600))
HEARTBEAT_TIMEOUT = int(os.getenv('HEARTBEAT_TIMEOUT', 90))
LOG_FILE = os.getenv('LOG_FILE')
TIMEZONE = os.getenv('TIMEZONE', 'Europe/Istanbul')

# ==================== LOGGING SETUP ====================
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ==================== GLOBAL STATE ====================
last_heartbeat = time.time()
thermostat_status = "UNKNOWN"
thermostat_mode = "AUTO"
alert_sent = False
arduino_serial = None

# ==================== FUNCTIONS ====================

def get_current_unix_time():
    """Get current Unix timestamp"""
    return int(time.time())

def sync_time_to_arduino(ser):
    """Send current time to Arduino"""
    try:
        unix_time = get_current_unix_time()
        current_dt = datetime.now(ZoneInfo(TIMEZONE))
        message = f"TIME:{unix_time}\n"
        ser.write(message.encode())
        logger.info(f"✓ Time synced to Arduino: {unix_time} (Local: {current_dt.strftime('%H:%M:%S')})")
    except Exception as e:
        logger.error(f"✗ Failed to sync time: {e}")

def heartbeat_monitor():
    """Monitor for missed heartbeats"""
    global last_heartbeat, alert_sent
    
    while True:
        time.sleep(10)
        
        time_since_heartbeat = time.time() - last_heartbeat
        
        if time_since_heartbeat > HEARTBEAT_TIMEOUT and not alert_sent:
            alert_sent = True
            logger.warning(f"⚠ ALERT: Thermostat offline - No heartbeat for {int(time_since_heartbeat)}s")
        
        elif time_since_heartbeat < HEARTBEAT_TIMEOUT and alert_sent:
            alert_sent = False
            logger.info("✓ Thermostat reconnected")

def read_arduino():
    """Read from Arduino serial"""
    global last_heartbeat, thermostat_status, thermostat_mode, arduino_serial
    
    while True:
        try:
            # Try to connect to Arduino
            arduino_serial = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=2)
            logger.info(f"✓ Connected to Arduino on {ARDUINO_PORT}")
            
            # Initial time sync
            time.sleep(2)
            sync_time_to_arduino(arduino_serial)
            
            while True:
                try:
                    if arduino_serial.in_waiting:
                        line = arduino_serial.readline().decode('utf-8').strip()
                        
                        if not line:
                            continue
                        
                        logger.info(f"Arduino: {line}")
                        
                        # Handle different message types
                        if line == "READY":
                            sync_time_to_arduino(arduino_serial)
                        
                        elif line == "TIME_SYNC_REQUEST":
                            sync_time_to_arduino(arduino_serial)
                        
                        elif line.startswith("TIME_SET:"):
                            logger.info("✓ Arduino confirmed time sync")
                        
                        elif line == "STATUS:STARTED":
                            last_heartbeat = time.time()
                            thermostat_status = "ON"
                        
                        elif line == "STATUS:STOPPED":
                            last_heartbeat = time.time()
                            thermostat_status = "OFF"
                        
                        elif line == "STATUS:STARTED_MANUAL":
                            last_heartbeat = time.time()
                            thermostat_status = "ON"
                        
                        elif line == "STATUS:STOPPED_MANUAL":
                            last_heartbeat = time.time()
                            thermostat_status = "OFF"
                        
                        elif line.startswith("MODE:"):
                            mode = line.replace("MODE:", "")
                            thermostat_mode = mode
                            logger.info(f"Mode changed to: {mode}")
                        
                        elif line.startswith("HEARTBEAT:"):
                            last_heartbeat = time.time()
                            # Parse: HEARTBEAT:HH:MM:ON/OFF:MODE
                            parts = line.split(":")
                            if len(parts) >= 4:
                                time_str = f"{parts[1]}:{parts[2]}"
                                status = parts[3]
                                thermostat_status = status
                                if len(parts) > 4:
                                    thermostat_mode = parts[4]
                                logger.debug(f"💓 Heartbeat - Time: {time_str}, Status: {status}, Mode: {thermostat_mode}")
                        
                        elif line.startswith("SCHED_UPDATED:"):
                            logger.info(f"Schedule updated: {line}")
                        
                        elif line == "SCHEDULES_CLEARED":
                            logger.info("All schedules cleared")
                        
                        elif line.startswith("ERROR:"):
                            error_msg = line.replace("ERROR:", "")
                            logger.error(f"✗ Arduino error: {error_msg}")
                
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    logger.error(f"✗ Read error: {e}")
                    time.sleep(1)
        
        except serial.SerialException as e:
            logger.error(f"✗ Serial connection failed: {e}")
            time.sleep(5)
            continue
        except Exception as e:
            logger.error(f"✗ Unexpected error: {e}")
            time.sleep(5)
            continue

# ==================== MAIN ====================
if __name__ == "__main__":
    import threading
    
    logger.info("=" * 50)
    logger.info("Smart Thermostat Manager Started")
    logger.info("=" * 50)
    
    # Start heartbeat monitor in background
    monitor_thread = threading.Thread(target=heartbeat_monitor, daemon=True)
    monitor_thread.start()
    
    # Start reading from Arduino (main loop)
    read_arduino()