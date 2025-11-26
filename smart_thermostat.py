#!/usr/bin/env python3
# Smart Thermostat - Arduino Manager
# Handles time sync, schedule management, and Arduino communication
# Receives commands from telegram_controller.py via socket

import serial
import time
import os
import socket
import threading
import json
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
COMMAND_PORT = 5000  # Socket port for receiving commands from telegram_controller

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

def send_arduino_command(command):
    """Send command to Arduino and return success status"""
    global arduino_serial
    try:
        if arduino_serial and arduino_serial.is_open:
            arduino_serial.write(f"{command}\n".encode())
            logger.info(f"→ Sent to Arduino: {command}")
            return True
        else:
            logger.error("✗ Cannot send command: Arduino not connected")
            return False
    except Exception as e:
        logger.error(f"✗ Error sending command to Arduino: {e}")
        return False

def handle_command_connection(client_socket, address):
    """Handle incoming command from telegram_controller"""
    try:
        client_socket.settimeout(5)
        data = client_socket.recv(4096).decode('utf-8').strip()

        if not data:
            return

        logger.info(f"← Received command: {data}")

        response = {"status": "error", "message": "Unknown command"}

        # Handle different command types
        if data.startswith("OVERRIDE:"):
            # Commands: OVERRIDE:ON, OVERRIDE:OFF, OVERRIDE:AUTO
            if send_arduino_command(data):
                response = {"status": "success", "message": f"Command sent: {data}"}
            else:
                response = {"status": "error", "message": "Failed to send to Arduino"}

        elif data.startswith("CLEAR_SCHED"):
            if send_arduino_command("CLEAR_SCHED"):
                response = {"status": "success", "message": "Schedules cleared"}
            else:
                response = {"status": "error", "message": "Failed to clear schedules"}

        elif data.startswith("SCHED:"):
            # Format: SCHED:index:startHour:startMinute:endHour:endMinute
            if send_arduino_command(data):
                response = {"status": "success", "message": f"Schedule sent: {data}"}
            else:
                response = {"status": "error", "message": "Failed to send schedule"}

        elif data == "GET_STATUS":
            response = {
                "status": "success",
                "thermostat_status": thermostat_status,
                "thermostat_mode": thermostat_mode,
                "last_heartbeat": last_heartbeat
            }

        else:
            response = {"status": "error", "message": f"Unknown command: {data}"}

        # Send response
        client_socket.sendall(json.dumps(response).encode('utf-8'))

    except socket.timeout:
        logger.warning("Command connection timeout")
    except Exception as e:
        logger.error(f"✗ Error handling command: {e}")
        try:
            error_response = json.dumps({"status": "error", "message": str(e)})
            client_socket.sendall(error_response.encode('utf-8'))
        except:
            pass
    finally:
        try:
            client_socket.close()
        except:
            pass

def command_server():
    """Socket server to receive commands from telegram_controller"""
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('localhost', COMMAND_PORT))
        server_socket.listen(5)

        logger.info(f"✓ Command server listening on port {COMMAND_PORT}")

        while True:
            try:
                client_socket, address = server_socket.accept()
                # Handle each command in a separate thread
                cmd_thread = threading.Thread(
                    target=handle_command_connection,
                    args=(client_socket, address),
                    daemon=True
                )
                cmd_thread.start()
            except Exception as e:
                logger.error(f"✗ Error accepting command connection: {e}")
                continue

    except Exception as e:
        logger.error(f"✗ Error starting command server: {e}")

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

    # Start command server in background
    command_thread = threading.Thread(target=command_server, daemon=True)
    command_thread.start()

    # Start heartbeat monitor in background
    monitor_thread = threading.Thread(target=heartbeat_monitor, daemon=True)
    monitor_thread.start()

    # Start reading from Arduino (main loop)
    read_arduino()