#!/usr/bin/env python3
# Telegram Controller - Sends commands to Arduino via serial

import serial
import time
import json
import os
import socket
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Load environment variables
load_dotenv(os.path.expanduser('~/.env'))

# Configuration from .env
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
ARDUINO_PORT = os.getenv('ARDUINO_PORT')
BAUD_RATE = int(os.getenv('BAUD_RATE', 9600))
schedule_file = os.getenv('SCHEDULE_FILE')
log_file = os.getenv('LOG_FILE')

# Global serial connection
arduino = None

# Global schedule storage
current_schedule = []

# Global state tracking
last_known_state = "OFF"
last_known_mode = "AUTO"
last_state_change = datetime.now()

def load_schedule():
    """Load schedule from JSON file"""
    global current_schedule
    try:
        with open(schedule_file, 'r') as f:
            data = json.load(f)
            current_schedule = data.get('schedules', [])
    except Exception as e:
        print(f"Error loading schedule: {e}")
        current_schedule = [
            {"name": "Morning", "startHour": 6, "startMinute": 0, "endHour": 8, "endMinute": 0},
            {"name": "Evening", "startHour": 17, "startMinute": 0, "endHour": 22, "endMinute": 0}
        ]
        save_schedule()

def save_schedule():
    """Save schedule to JSON file"""
    try:
        with open(schedule_file, 'w') as f:
            json.dump({'schedules': current_schedule}, f, indent=2)
    except Exception as e:
        print(f"Error saving schedule: {e}")

def send_schedule_to_arduino():
    """Send all schedules to Arduino"""
    try:
        arduino.write(b"CLEAR_SCHED\n")
        time.sleep(0.2)
        
        for i, sched in enumerate(current_schedule):
            message = f"SCHED:{i}:{sched['startHour']}:{sched['startMinute']}:{sched['endHour']}:{sched['endMinute']}\n"
            arduino.write(message.encode())
            time.sleep(0.2)
    except Exception as e:
        print(f"Error sending schedule: {e}")

def reconnect_arduino():
    """Try to reconnect to Arduino"""
    global arduino
    try:
        if arduino:
            arduino.close()
    except:
        pass
    
    try:
        arduino = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1)
        print("Reconnected to Arduino")
        time.sleep(1)
        send_schedule_to_arduino()
        return True
    except:
        print("Failed to reconnect")
        return False

async def cmd_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /on command"""
    global last_known_state, last_known_mode, last_state_change
    try:
        arduino.write(b"OVERRIDE:ON\n")
        last_known_state = "ON"
        last_known_mode = "MANUAL_ON"
        last_state_change = datetime.now()
        await update.message.reply_text("🔥 Thermostat turned ON manually")
    except Exception as e:
        if reconnect_arduino():
            try:
                arduino.write(b"OVERRIDE:ON\n")
                last_known_state = "ON"
                last_known_mode = "MANUAL_ON"
                last_state_change = datetime.now()
                await update.message.reply_text("🔥 Thermostat turned ON manually (reconnected)")
            except:
                await update.message.reply_text(f"❌ Error: Arduino disconnected")
        else:
            await update.message.reply_text(f"❌ Error: Cannot connect to Arduino")

async def cmd_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /off command"""
    global last_known_state, last_known_mode, last_state_change
    try:
        arduino.write(b"OVERRIDE:OFF\n")
        last_known_state = "OFF"
        last_known_mode = "MANUAL_OFF"
        last_state_change = datetime.now()
        await update.message.reply_text("❄️ Thermostat turned OFF manually")
    except Exception as e:
        if reconnect_arduino():
            try:
                arduino.write(b"OVERRIDE:OFF\n")
                last_known_state = "OFF"
                last_known_mode = "MANUAL_OFF"
                last_state_change = datetime.now()
                await update.message.reply_text("❄️ Thermostat turned OFF manually (reconnected)")
            except:
                await update.message.reply_text(f"❌ Error: Arduino disconnected")
        else:
            await update.message.reply_text(f"❌ Error: Cannot connect to Arduino")

async def cmd_auto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /auto command"""
    global last_known_mode, last_state_change
    try:
        arduino.write(b"OVERRIDE:AUTO\n")
        last_known_mode = "AUTO"
        last_state_change = datetime.now()
        await update.message.reply_text("🔄 Thermostat set to AUTO mode (following schedule)")
    except Exception as e:
        if reconnect_arduino():
            try:
                arduino.write(b"OVERRIDE:AUTO\n")
                last_known_mode = "AUTO"
                last_state_change = datetime.now()
                await update.message.reply_text("🔄 Thermostat set to AUTO mode (reconnected)")
            except:
                await update.message.reply_text(f"❌ Error: Arduino disconnected")
        else:
            await update.message.reply_text(f"❌ Error: Cannot connect to Arduino")

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command - get actual status from log file"""
    try:
        if not update.message:
            return
        
        # Get last heartbeat from log
        last_heartbeat_info = None
        
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                for line in reversed(lines):
                    if "HEARTBEAT:" in line and "Arduino:" in line:
                        parts = line.split("HEARTBEAT:")
                        if len(parts) > 1:
                            heartbeat_data = parts[1].strip()
                            hb_parts = heartbeat_data.split(":")
                            if len(hb_parts) >= 3:
                                arduino_time = f"{hb_parts[0]}:{hb_parts[1]}"
                                state = hb_parts[2]
                                mode = hb_parts[3] if len(hb_parts) > 3 else "UNKNOWN"
                                timestamp_match = line[1:20]
                                
                                last_heartbeat_info = {
                                    'time': arduino_time,
                                    'state': state,
                                    'mode': mode,
                                    'log_time': timestamp_match
                                }
                                break
        except Exception as e:
            print(f"Error reading log: {e}")
        
        current_time = datetime.now()
        
        if last_heartbeat_info:
            status_message = f"""
📊 <b>Thermostat Status (Live)</b>

🔥 State: <b>{last_heartbeat_info['state']}</b>
⚙️ Mode: <b>{last_heartbeat_info['mode']}</b>
🕐 Arduino Time: <b>{last_heartbeat_info['time']}</b>
🕐 System Time: <b>{current_time.strftime('%H:%M:%S')}</b>
📝 Last Update: <b>{last_heartbeat_info['log_time']}</b>

<i>Status from system logs</i>"""
        else:
            status_message = f"""
📊 <b>Thermostat Status</b>

⚠️ <i>No recent heartbeat found</i>
🕐 System Time: <b>{current_time.strftime('%H:%M:%S')}</b>

<i>Check if smart_thermostat.py is running</i>"""
        
        await update.message.reply_text(status_message, parse_mode='HTML')
        
    except Exception as e:
        if update.message:
            await update.message.reply_text(f"❌ Error: {e}")

async def cmd_debug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Debug command - show system info"""
    try:
        debug_text = f"""
🔧 <b>System Debug Info</b>

✅ Telegram Bot: Connected
⚙️ Last Mode: {last_known_mode}
🔥 Last State: {last_known_state}
🕐 Last Change: {last_state_change.strftime('%H:%M:%S')}

📝 Schedules Loaded: {len(current_schedule)}

<i>All systems operational</i>
"""
        await update.message.reply_text(debug_text, parse_mode='HTML')
    except Exception as e:
        await update.message.reply_text(f"❌ Debug error: {e}")

async def cmd_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /schedule command - show current schedule"""
    load_schedule()
    
    schedule_text = "📅 <b>Current Schedule</b>\n\n"
    for i, sched in enumerate(current_schedule):
        start_time = f"{sched['startHour']:02d}:{sched['startMinute']:02d}"
        end_time = f"{sched['endHour']:02d}:{sched['endMinute']:02d}"
        schedule_text += f"{i+1}. {sched.get('name', f'Schedule {i+1}')}: {start_time} - {end_time}\n"
    
    schedule_text += "\n<b>To modify:</b>\n/edit 1 06 00 08 00"
    await update.message.reply_text(schedule_text, parse_mode='HTML')

async def cmd_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /edit command - modify schedule"""
    try:
        args = context.args
        if len(args) != 5:
            await update.message.reply_text("❌ Format: /edit [number] [startHour] [startMin] [endHour] [endMin]")
            return
        
        index = int(args[0]) - 1
        start_hour = int(args[1])
        start_min = int(args[2])
        end_hour = int(args[3])
        end_min = int(args[4])
        
        load_schedule()
        
        if index < 0 or index >= len(current_schedule):
            await update.message.reply_text(f"❌ Invalid schedule number.")
            return
        
        current_schedule[index]['startHour'] = start_hour
        current_schedule[index]['startMinute'] = start_min
        current_schedule[index]['endHour'] = end_hour
        current_schedule[index]['endMinute'] = end_min
        
        save_schedule()
        send_schedule_to_arduino()
        
        start_time = f"{start_hour:02d}:{start_min:02d}"
        end_time = f"{end_hour:02d}:{end_min:02d}"
        await update.message.reply_text(f"✅ Schedule {index+1} updated to {start_time} - {end_time}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def cmd_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /add command - add new schedule"""
    try:
        args = context.args
        if len(args) < 4:
            await update.message.reply_text("❌ Format: /add [startHour] [startMin] [endHour] [endMin] [name]")
            return
        
        start_hour = int(args[0])
        start_min = int(args[1])
        end_hour = int(args[2])
        end_min = int(args[3])
        name = " ".join(args[4:]) if len(args) > 4 else f"Schedule {len(current_schedule)+1}"
        
        load_schedule()
        
        if len(current_schedule) >= 5:
            await update.message.reply_text("❌ Maximum 5 schedules allowed.")
            return
        
        new_schedule = {
            "name": name,
            "startHour": start_hour,
            "startMinute": start_min,
            "endHour": end_hour,
            "endMinute": end_min
        }
        
        current_schedule.append(new_schedule)
        save_schedule()
        send_schedule_to_arduino()
        
        start_time = f"{start_hour:02d}:{start_min:02d}"
        end_time = f"{end_hour:02d}:{end_min:02d}"
        await update.message.reply_text(f"✅ New schedule added: {name} ({start_time} - {end_time})")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def cmd_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /delete command - remove schedule"""
    try:
        args = context.args
        if len(args) != 1:
            await update.message.reply_text("❌ Format: /delete [number]")
            return
        
        index = int(args[0]) - 1
        load_schedule()
        
        if index < 0 or index >= len(current_schedule):
            await update.message.reply_text(f"❌ Invalid schedule number.")
            return
        
        removed = current_schedule.pop(index)
        save_schedule()
        send_schedule_to_arduino()
        
        await update.message.reply_text(f"✅ Schedule '{removed.get('name')}' deleted")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = """
🤖 <b>Smart Thermostat Commands</b>

<b>🔥 Control:</b>
/on - Turn ON
/off - Turn OFF
/auto - Auto mode
/status - Check status

<b>📅 Schedule:</b>
/schedule - View schedules
/edit - Edit schedule
/add - Add schedule
/delete - Delete schedule

/help - Show this message
"""
    await update.message.reply_text(help_text, parse_mode='HTML')

def request_summary_service(command):
    """Request data from summary service"""
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(30)  # Increase timeout to 30 seconds
        client.connect(('localhost', 9999))
        client.sendall(command.encode('utf-8'))
        response = client.recv(8192).decode('utf-8')
        client.close()
        return json.loads(response)
    except socket.timeout:
        print("Summary service timeout - calculation taking too long")
        return {'status': 'error', 'message': 'Calculation timeout - logs too large'}
    except Exception as e:
        print(f"Error connecting to summary service: {e}")
        return {'status': 'error', 'message': str(e)}

def format_summary_message(summary_data):
    """Format summary data into Telegram message"""
    if summary_data['status'] != 'success':
        return "⚠️ Error calculating summary"
    
    today = summary_data['today']
    yesterday = summary_data['yesterday']
    day_before = summary_data['day_before']
    last_7 = summary_data['last_7_days']
    
    message = f"""
📊 <b>Thermostat Runtime Summary</b>

📅 <b>Today</b> ({today['date']}):
   ⏱️ {today['runtime_formatted']} ({today['sessions']} sessions)

📅 <b>Yesterday</b> ({yesterday['date']}):
   ⏱️ {yesterday['runtime_formatted']} ({yesterday['sessions']} sessions)

📅 <b>Day Before</b> ({day_before['date']}):
   ⏱️ {day_before['runtime_formatted']} ({day_before['sessions']} sessions)

📊 <b>Last 7 Days</b>:
   ⏱️ {last_7['runtime_formatted']} ({last_7['sessions']} sessions)
   📈 Average: {last_7['average_per_day']}/day

🕐 Updated: {summary_data['timestamp'][:16]}
"""
    return message

async def cmd_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /summary command"""
    try:
        if not update.message:
            return
        
        # Request summary from service
        summary_data = request_summary_service("SUMMARY")
        
        # Format and send
        message = format_summary_message(summary_data)
        await update.message.reply_text(message, parse_mode='HTML')
    
    except Exception as e:
        if update.message:
            await update.message.reply_text(f"❌ Error: {e}")

async def send_daily_summary():
    """Send daily summary at 23:55"""
    try:
        # Request summary service to save daily summary (with longer timeout)
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(60)  # 60 seconds for daily summary
        client.connect(('localhost', 9999))
        client.sendall(b'DAILY_SUMMARY')
        result = client.recv(1024).decode('utf-8')
        client.close()
        
        # Get the summary to send
        summary_data = request_summary_service("SUMMARY")
        message = format_summary_message(summary_data)
        
        # Send to Telegram
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        requests.post(url, json=payload, timeout=10)
        print(f"✓ Daily summary sent at 23:55")
    
    except socket.timeout:
        print("✗ Daily summary timeout")
    except Exception as e:
        print(f"✗ Error sending daily summary: {e}")

def setup_scheduler():
    """Setup APScheduler for daily summary at 23:55"""
    try:
        scheduler = BackgroundScheduler()
        scheduler.add_job(send_daily_summary, 'cron', hour=23, minute=55)
        scheduler.start()
        print("✓ Daily summary scheduler started (23:55)")
        return scheduler
    except Exception as e:
        print(f"✗ Error setting up scheduler: {e}")
        return None

if __name__ == "__main__":
    try:
        arduino = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1)
        print(f"Connected to Arduino on {ARDUINO_PORT}")
        
        load_schedule()
        time.sleep(1)
        send_schedule_to_arduino()
    except Exception as e:
        print(f"Failed to connect to Arduino: {e}")
        exit(1)
    
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("on", cmd_on))
    application.add_handler(CommandHandler("off", cmd_off))
    application.add_handler(CommandHandler("auto", cmd_auto))
    application.add_handler(CommandHandler("status", cmd_status))
    application.add_handler(CommandHandler("debug", cmd_debug))
    application.add_handler(CommandHandler("schedule", cmd_schedule))
    application.add_handler(CommandHandler("edit", cmd_edit))
    application.add_handler(CommandHandler("add", cmd_add))
    application.add_handler(CommandHandler("delete", cmd_delete))
    application.add_handler(CommandHandler("help", cmd_help))
    application.add_handler(CommandHandler("start", cmd_help))
    application.add_handler(CommandHandler("summary", cmd_summary))
    
    scheduler = setup_scheduler()
    
    print("Telegram bot started. Press Ctrl+C to stop.")
    print("Available commands: /on, /off, /auto, /status, /debug, /schedule, /edit, /add, /delete, /help, /summary")
    
    try:
        application.run_polling(drop_pending_updates=True)
    finally:
        if scheduler:
            scheduler.shutdown()

