// Arduino UNO - Smart Thermostat Controller with Manual Override & Dynamic Schedules
// FIXED: Proper timezone handling for Turkey (UTC+3)
// Accepts time sync: TIME:1234567890 (Unix timestamp)
// Accepts overrides: OVERRIDE:ON, OVERRIDE:OFF, OVERRIDE:AUTO
// Accepts schedule updates: SCHED:index:startHour:startMinute:endHour:endMinute

#include <TimeLib.h>

// Relay pins
const int RELAY1_PIN = 5;
const int RELAY2_PIN = 6;

// Turkey timezone offset (UTC+3)
const int TIMEZONE_OFFSET = 3 * 3600; // 3 hours in seconds

// Status variables
bool thermostatActive = false;
unsigned long lastHeartbeat = 0;
const unsigned long HEARTBEAT_INTERVAL = 30000; // 30 seconds
bool timeIsSet = false;

// Override mode variables
enum Mode {
  MODE_AUTO,
  MODE_MANUAL_ON,
  MODE_MANUAL_OFF
};
Mode currentMode = MODE_AUTO;

// Schedule (24-hour format) - can be updated via serial
struct Schedule {
  int startHour;
  int startMinute;
  int endHour;
  int endMinute;
  bool active;  // Whether this schedule slot is active
};

// Support up to 5 schedules
Schedule schedules[5] = {
  {6, 0, 8, 0, true},      // 6:00 AM - 8:00 AM
  {17, 0, 22, 0, true},    // 5:00 PM - 10:00 PM
  {0, 0, 0, 0, false},     // Empty slot
  {0, 0, 0, 0, false},     // Empty slot
  {0, 0, 0, 0, false}      // Empty slot
};
const int MAX_SCHEDULES = 5;
int activeScheduleCount = 2;  // Start with 2 active schedules

void setup() {
  Serial.begin(9600);
  
  pinMode(RELAY1_PIN, OUTPUT);
  pinMode(RELAY2_PIN, OUTPUT);
  digitalWrite(RELAY1_PIN, HIGH); // Relays off (active low)
  digitalWrite(RELAY2_PIN, HIGH);
  
  Serial.println("READY");
  Serial.println("TIME_SYNC_REQUEST");
}

void loop() {
  // Check for serial input
  if (Serial.available()) {
    processSerialData();
  }
  
  // Only operate if time is set
  if (!timeIsSet) {
    // Request time sync every 5 seconds until we get it
    static unsigned long lastRequest = 0;
    if (millis() - lastRequest > 5000) {
      Serial.println("TIME_SYNC_REQUEST");
      lastRequest = millis();
    }
    return;
  }
  
  // Handle thermostat logic based on current mode
  if (currentMode == MODE_AUTO) {
    // AUTO MODE: Follow schedule
    int currentHour = hour();
    int currentMinute = minute();
    
    bool shouldBeActive = false;
    
    // Check if current time matches any active schedule
    for (int i = 0; i < MAX_SCHEDULES; i++) {
      if (!schedules[i].active) continue;  // Skip inactive schedules
      
      int startTotalMinutes = schedules[i].startHour * 60 + schedules[i].startMinute;
      int endTotalMinutes = schedules[i].endHour * 60 + schedules[i].endMinute;
      int currentTotalMinutes = currentHour * 60 + currentMinute;
      
      if (currentTotalMinutes >= startTotalMinutes && currentTotalMinutes < endTotalMinutes) {
        shouldBeActive = true;
        break;
      }
    }
    
    // State change detection for AUTO mode
    if (shouldBeActive && !thermostatActive) {
      activateThermostat();
      thermostatActive = true;
      Serial.println("STATUS:STARTED");
    } 
    else if (!shouldBeActive && thermostatActive) {
      deactivateThermostat();
      thermostatActive = false;
      Serial.println("STATUS:STOPPED");
    }
  }
  else if (currentMode == MODE_MANUAL_ON) {
    // MANUAL ON: Keep thermostat on regardless of schedule
    if (!thermostatActive) {
      activateThermostat();
      thermostatActive = true;
    }
  }
  else if (currentMode == MODE_MANUAL_OFF) {
    // MANUAL OFF: Keep thermostat off regardless of schedule
    if (thermostatActive) {
      deactivateThermostat();
      thermostatActive = false;
    }
  }
  
  // Send heartbeat every 30 seconds
  if (millis() - lastHeartbeat >= HEARTBEAT_INTERVAL) {
    sendHeartbeat();
    lastHeartbeat = millis();
  }
  
  // Request time sync every hour to correct any drift
  static unsigned long lastTimeSync = 0;
  if (millis() - lastTimeSync > 3600000) { // 1 hour
    Serial.println("TIME_SYNC_REQUEST");
    lastTimeSync = millis();
  }
  
  delay(100);
}

void processSerialData() {
  String input = Serial.readStringUntil('\n');
  input.trim(); // Remove any whitespace
  
  if (input.startsWith("TIME:")) {
    // Time sync from Pi - Unix timestamp in UTC
    unsigned long utcTimestamp = input.substring(5).toInt();
    
    // Convert UTC to Turkey time (UTC+3) by adding offset
    time_t turkeyTime = utcTimestamp + TIMEZONE_OFFSET;
    
    setTime(turkeyTime);
    timeIsSet = true;
    
    // Send confirmation with local time
    Serial.print("TIME_SET:");
    Serial.print(utcTimestamp);
    Serial.print(":");
    if (hour() < 10) Serial.print("0");
    Serial.print(hour());
    Serial.print(":");
    if (minute() < 10) Serial.print("0");
    Serial.println(minute());
  }
  else if (input.startsWith("SCHED:")) {
    // Schedule update format: SCHED:index:startHour:startMinute:endHour:endMinute
    int colonIndex = 6;  // Start after "SCHED:"
    
    // Parse index
    int nextColon = input.indexOf(':', colonIndex);
    int index = input.substring(colonIndex, nextColon).toInt();
    colonIndex = nextColon + 1;
    
    if (index >= 0 && index < MAX_SCHEDULES) {
      // Parse startHour
      nextColon = input.indexOf(':', colonIndex);
      schedules[index].startHour = input.substring(colonIndex, nextColon).toInt();
      colonIndex = nextColon + 1;
      
      // Parse startMinute
      nextColon = input.indexOf(':', colonIndex);
      schedules[index].startMinute = input.substring(colonIndex, nextColon).toInt();
      colonIndex = nextColon + 1;
      
      // Parse endHour
      nextColon = input.indexOf(':', colonIndex);
      schedules[index].endHour = input.substring(colonIndex, nextColon).toInt();
      colonIndex = nextColon + 1;
      
      // Parse endMinute
      schedules[index].endMinute = input.substring(colonIndex).toInt();
      
      // Mark as active
      schedules[index].active = true;
      
      // Update active count
      updateActiveScheduleCount();
      
      Serial.print("SCHED_UPDATED:");
      Serial.print(index);
      Serial.print(":");
      Serial.print(schedules[index].startHour);
      Serial.print(":");
      Serial.print(schedules[index].startMinute);
      Serial.print("-");
      Serial.print(schedules[index].endHour);
      Serial.print(":");
      Serial.println(schedules[index].endMinute);
    }
  }
  else if (input == "CLEAR_SCHED") {
    // Clear all schedules
    for (int i = 0; i < MAX_SCHEDULES; i++) {
      schedules[i].active = false;
    }
    activeScheduleCount = 0;
    Serial.println("SCHEDULES_CLEARED");
  }
  else if (input == "OVERRIDE:ON") {
    currentMode = MODE_MANUAL_ON;
    Serial.println("MODE:MANUAL_ON");
    if (!thermostatActive) {
      activateThermostat();
      thermostatActive = true;
      Serial.println("STATUS:STARTED_MANUAL");
    }
  }
  else if (input == "OVERRIDE:OFF") {
    currentMode = MODE_MANUAL_OFF;
    Serial.println("MODE:MANUAL_OFF");
    if (thermostatActive) {
      deactivateThermostat();
      thermostatActive = false;
      Serial.println("STATUS:STOPPED_MANUAL");
    }
  }
  else if (input == "OVERRIDE:AUTO") {
    currentMode = MODE_AUTO;
    Serial.println("MODE:AUTO");
    // Will be handled in next loop iteration
  }
  else if (input == "STATUS") {
    // Respond with current status
    sendStatus();
  }
  else if (input == "GET_SCHEDULES") {
    // Send all active schedules
    sendSchedules();
  }
}

void updateActiveScheduleCount() {
  activeScheduleCount = 0;
  for (int i = 0; i < MAX_SCHEDULES; i++) {
    if (schedules[i].active) {
      activeScheduleCount++;
    }
  }
}

void activateThermostat() {
  digitalWrite(RELAY1_PIN, LOW);  // Turn on relay 1
  // digitalWrite(RELAY2_PIN, LOW);  // Turn on relay 2
}

void deactivateThermostat() {
  digitalWrite(RELAY1_PIN, HIGH); // Turn off relay 1
  digitalWrite(RELAY2_PIN, HIGH); // Turn off relay 2
}

void sendHeartbeat() {
  Serial.print("HEARTBEAT:");
  if (hour() < 10) Serial.print("0");
  Serial.print(hour());
  Serial.print(":");
  if (minute() < 10) Serial.print("0");
  Serial.print(minute());
  Serial.print(":");
  Serial.print(thermostatActive ? "ON" : "OFF");
  Serial.print(":");
  
  // Include mode in heartbeat
  switch(currentMode) {
    case MODE_AUTO:
      Serial.println("AUTO");
      break;
    case MODE_MANUAL_ON:
      Serial.println("MANUAL_ON");
      break;
    case MODE_MANUAL_OFF:
      Serial.println("MANUAL_OFF");
      break;
  }
}

void sendStatus() {
  Serial.print("CURRENT_STATUS:");
  Serial.print(thermostatActive ? "ON" : "OFF");
  Serial.print(":");
  switch(currentMode) {
    case MODE_AUTO:
      Serial.print("AUTO");
      break;
    case MODE_MANUAL_ON:
      Serial.print("MANUAL_ON");
      break;
    case MODE_MANUAL_OFF:
      Serial.print("MANUAL_OFF");
      break;
  }
  Serial.print(":");
  if (hour() < 10) Serial.print("0");
  Serial.print(hour());
  Serial.print(":");
  if (minute() < 10) Serial.print("0");
  Serial.println(minute());
}

void sendSchedules() {
  Serial.print("SCHEDULES:");
  Serial.println(activeScheduleCount);
  
  for (int i = 0; i < MAX_SCHEDULES; i++) {
    if (schedules[i].active) {
      Serial.print("SCHED_ITEM:");
      Serial.print(i);
      Serial.print(":");
      Serial.print(schedules[i].startHour);
      Serial.print(":");
      Serial.print(schedules[i].startMinute);
      Serial.print(":");
      Serial.print(schedules[i].endHour);
      Serial.print(":");
      Serial.println(schedules[i].endMinute);
    }
  }
}
