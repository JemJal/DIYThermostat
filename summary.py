#!/usr/bin/env python3
# Smart Thermostat Summary Service
# Parses logs, calculates runtime statistics, and manages summary data
# Runs as a daemon service

import os
import json
import socket
import threading
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
import logging
import sys
import socket
import json
from apscheduler.schedulers.background import BackgroundScheduler

# Load environment variables
load_dotenv(os.path.expanduser('~/.env'))

# Configuration
LOG_FILE = os.getenv('LOG_FILE')
TIMEZONE = os.getenv('TIMEZONE', 'Europe/Istanbul')
SUMMARY_FILE = os.path.expanduser('~/thermostat_summary.json')
SOCKET_FILE = os.path.expanduser('~/thermostat_summary.sock')
SUMMARY_PORT = 9999

# ==================== LOGGING SETUP ====================
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(os.path.expanduser('~/thermostat_summary.log')),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ==================== DATA STRUCTURES ====================

class ThermostatSession:
    """Represents a single on/off session"""
    def __init__(self, start_time, end_time=None, session_type="AUTO"):
        self.start_time = start_time
        self.end_time = end_time
        self.session_type = session_type  # AUTO or MANUAL
    
    def duration_seconds(self):
        """Get duration in seconds"""
        if self.end_time is None:
            return None
        return int((self.end_time - self.start_time).total_seconds())
    
    def is_complete(self):
        """Check if session has both start and end"""
        return self.end_time is not None

# ==================== LOG PARSING ====================

def parse_logs():
    """
    Parse log file and extract all thermostat sessions
    Returns list of ThermostatSession objects
    """
    sessions = []
    current_session = None
    
    try:
        with open(LOG_FILE, 'r') as f:
            lines = f.readlines()
        
        for line in lines:
            try:
                # Skip lines without status info
                if "STATUS:" not in line and "MODE:" not in line:
                    continue
                
                # Extract timestamp: [2025-11-19 17:22:13,897]
                if not line.startswith('['):
                    continue
                
                timestamp_str = line[1:20]  # Extract YYYY-MM-DD HH:MM:SS
                try:
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                    timestamp = timestamp.replace(tzinfo=ZoneInfo(TIMEZONE))
                except ValueError:
                    continue
                
                # Parse status messages
                if "STATUS:STARTED" in line:
                    # Close previous session if exists
                    if current_session and not current_session.is_complete():
                        current_session.end_time = timestamp
                        sessions.append(current_session)
                    
                    # Determine session type
                    session_type = "MANUAL" if "MANUAL" in line else "AUTO"
                    current_session = ThermostatSession(timestamp, session_type=session_type)
                
                elif "STATUS:STOPPED" in line:
                    if current_session and not current_session.is_complete():
                        current_session.end_time = timestamp
                        sessions.append(current_session)
                        current_session = None
            
            except Exception as e:
                logger.warning(f"Error parsing line: {e}")
                continue
        
        # Handle incomplete session at end of file
        if current_session and not current_session.is_complete():
            logger.warning("Incomplete session at end of log file")
            # Don't add incomplete sessions
        
        logger.info(f"✓ Parsed {len(sessions)} complete sessions from logs")
        return sessions
    
    except FileNotFoundError:
        logger.error(f"Log file not found: {LOG_FILE}")
        return []
    except Exception as e:
        logger.error(f"Error parsing logs: {e}")
        return []

# ==================== CALCULATIONS ====================

def get_date_range(start_date, end_date):
    """Get all dates between start and end (inclusive)"""
    current = start_date
    dates = []
    while current <= end_date:
        dates.append(current)
        current += timedelta(days=1)
    return dates

def calculate_runtime_for_period(sessions, start_datetime, end_datetime):
    """
    Calculate total runtime for a specific period
    Returns: (total_seconds, session_count, sessions_list)
    """
    total_seconds = 0
    session_count = 0
    period_sessions = []
    
    for session in sessions:
        # Check if session overlaps with period
        if session.end_time < start_datetime or session.start_time > end_datetime:
            continue
        
        # Calculate overlap duration
        overlap_start = max(session.start_time, start_datetime)
        overlap_end = min(session.end_time, end_datetime)
        
        overlap_duration = int((overlap_end - overlap_start).total_seconds())
        
        if overlap_duration > 0:
            total_seconds += overlap_duration
            session_count += 1
            period_sessions.append({
                'start': overlap_start.isoformat(),
                'end': overlap_end.isoformat(),
                'duration': overlap_duration,
                'type': session.session_type
            })
    
    return total_seconds, session_count, period_sessions

def format_seconds(seconds):
    """Convert seconds to human readable format"""
    if seconds is None:
        return "N/A"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    
    if hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"

def get_summary():
    """
    Calculate summary statistics
    Returns dictionary with all statistics
    """
    try:
        sessions = parse_logs()
        
        if not sessions:
            return {
                'status': 'error',
                'message': 'No sessions found in logs'
            }
        
        # Get timezone-aware now
        now = datetime.now(ZoneInfo(TIMEZONE))
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Calculate periods
        yesterday_start = today_start - timedelta(days=1)
        yesterday_end = today_start - timedelta(seconds=1)
        
        day_before_start = today_start - timedelta(days=2)
        day_before_end = yesterday_start - timedelta(seconds=1)
        
        seven_days_start = today_start - timedelta(days=6)  # 7 days including today
        seven_days_end = now
        
        today_end = now
        
        # Calculate runtimes
        today_seconds, today_sessions, today_details = calculate_runtime_for_period(
            sessions, today_start, today_end
        )
        
        yesterday_seconds, yesterday_sessions, yesterday_details = calculate_runtime_for_period(
            sessions, yesterday_start, yesterday_end
        )
        
        day_before_seconds, day_before_sessions, day_before_details = calculate_runtime_for_period(
            sessions, day_before_start, day_before_end
        )
        
        seven_days_seconds, seven_days_sessions, seven_days_details = calculate_runtime_for_period(
            sessions, seven_days_start, seven_days_end
        )
        
        # Calculate averages
        days_with_data = 7
        average_seconds = seven_days_seconds // days_with_data if days_with_data > 0 else 0
        
        result = {
            'status': 'success',
            'timestamp': now.isoformat(),
            'today': {
                'date': today_start.strftime('%Y-%m-%d'),
                'runtime_seconds': today_seconds,
                'runtime_formatted': format_seconds(today_seconds),
                'sessions': today_sessions
            },
            'yesterday': {
                'date': yesterday_start.strftime('%Y-%m-%d'),
                'runtime_seconds': yesterday_seconds,
                'runtime_formatted': format_seconds(yesterday_seconds),
                'sessions': yesterday_sessions
            },
            'day_before': {
                'date': day_before_start.strftime('%Y-%m-%d'),
                'runtime_seconds': day_before_seconds,
                'runtime_formatted': format_seconds(day_before_seconds),
                'sessions': day_before_sessions
            },
            'last_7_days': {
                'runtime_seconds': seven_days_seconds,
                'runtime_formatted': format_seconds(seven_days_seconds),
                'sessions': seven_days_sessions,
                'average_per_day': format_seconds(average_seconds)
            }
        }
        
        logger.info(f"✓ Summary calculated successfully")
        return result
    
    except Exception as e:
        logger.error(f"Error calculating summary: {e}")
        return {
            'status': 'error',
            'message': str(e)
        }

# ==================== SUMMARY FILE MANAGEMENT ====================

def load_summary_file():
    """Load existing summary.json"""
    try:
        if os.path.exists(SUMMARY_FILE):
            with open(SUMMARY_FILE, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"Error loading summary file: {e}")
        return {}

def save_summary_file(data):
    """Save summary.json"""
    try:
        with open(SUMMARY_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"✓ Summary file saved")
        return True
    except Exception as e:
        logger.error(f"Error saving summary file: {e}")
        return False

def add_daily_summary():
    """
    Add today's summary to summary.json
    Called daily at 23:55
    """
    try:
        summary = get_summary()
        
        if summary['status'] != 'success':
            logger.error("Cannot add daily summary - calculation failed")
            return False
        
        today_date = summary['today']['date']
        
        # Load existing summaries
        summaries = load_summary_file()
        
        # Add or update today's entry
        summaries[today_date] = {
            'runtime_seconds': summary['today']['runtime_seconds'],
            'runtime_formatted': summary['today']['runtime_formatted'],
            'sessions': summary['today']['sessions'],
            'timestamp': summary['timestamp']
        }
        
        # Save back to file
        if save_summary_file(summaries):
            logger.info(f"✓ Daily summary added for {today_date}")
            return True
        return False
    
    except Exception as e:
        logger.error(f"Error adding daily summary: {e}")
        return False

def get_historical_summary():
    """Get all historical summaries from file"""
    try:
        summaries = load_summary_file()
        return {
            'status': 'success',
            'summaries': summaries
        }
    except Exception as e:
        logger.error(f"Error getting historical summary: {e}")
        return {
            'status': 'error',
            'message': str(e)
        }

# ==================== SOCKET SERVER ====================

def handle_client(client_socket, address):
    """Handle incoming client requests"""
    try:
        client_socket.settimeout(60)  # Allow 60 seconds for processing
        # Receive request
        request = client_socket.recv(1024).decode('utf-8').strip()
        
        logger.debug(f"Received request from {address}: {request}")
        
        response = {}
        
        if request == "SUMMARY":
            logger.info("Calculating summary...")
            response = get_summary()
        
        elif request == "DAILY_SUMMARY":
            logger.info("Adding daily summary...")
            response = add_daily_summary()
        
        elif request == "HISTORICAL":
            logger.info("Retrieving historical summaries...")
            response = get_historical_summary()
        
        else:
            response = {
                'status': 'error',
                'message': f'Unknown command: {request}'
            }
        
        # Send response
        response_json = json.dumps(response)
        client_socket.sendall(response_json.encode('utf-8'))
        
    except socket.timeout:
        logger.error(f"Client timeout from {address}")
        try:
            error_response = json.dumps({'status': 'error', 'message': 'Processing timeout'})
            client_socket.sendall(error_response.encode('utf-8'))
        except:
            pass
    except Exception as e:
        logger.error(f"Error handling client: {e}")
        try:
            error_response = json.dumps({'status': 'error', 'message': str(e)})
            client_socket.sendall(error_response.encode('utf-8'))
        except:
            pass
    
    finally:
        client_socket.close()

def start_server():
    """Start TCP socket server"""
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('localhost', SUMMARY_PORT))
        server_socket.listen(5)
        
        logger.info(f"✓ Summary service listening on port {SUMMARY_PORT}")
        
        while True:
            try:
                client_socket, address = server_socket.accept()
                client_thread = threading.Thread(
                    target=handle_client,
                    args=(client_socket, address),
                    daemon=True
                )
                client_thread.start()
            
            except KeyboardInterrupt:
                logger.info("Summary service shutting down...")
                break
            except Exception as e:
                logger.error(f"Error accepting connection: {e}")
                continue
    
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        return False
    
    finally:
        try:
            server_socket.close()
        except:
            pass
    
    return True

# ==================== CLIENT FUNCTIONS ====================

def request_summary():
    """Request summary from service"""
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('localhost', SUMMARY_PORT))
        client.sendall(b'SUMMARY')
        response = client.recv(4096).decode('utf-8')
        client.close()
        return json.loads(response)
    except Exception as e:
        logger.error(f"Error requesting summary: {e}")
        return {'status': 'error', 'message': str(e)}

def request_daily_summary():
    """Request daily summary save"""
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('localhost', SUMMARY_PORT))
        client.sendall(b'DAILY_SUMMARY')
        response = client.recv(1024).decode('utf-8')
        client.close()
        return json.loads(response)
    except Exception as e:
        logger.error(f"Error requesting daily summary: {e}")
        return {'status': 'error', 'message': str(e)}

def request_historical():
    """Request historical summaries"""
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('localhost', SUMMARY_PORT))
        client.sendall(b'HISTORICAL')
        response = client.recv(8192).decode('utf-8')
        client.close()
        return json.loads(response)
    except Exception as e:
        logger.error(f"Error requesting historical: {e}")
        return {'status': 'error', 'message': str(e)}

# ==================== MAIN ====================

if __name__ == "__main__":
    import sys
    
    logger.info("=" * 50)
    logger.info("Smart Thermostat Summary Service Started")
    logger.info("=" * 50)
    
    # Start server
    start_server()