/*
====================================================================
              B.R.A.V.E. FINAL MASTER V7
       Belt Rupture Analysis & Vulnerability Estimation

                    ESP32 SENSOR NODE

--------------------------------------------------------------------
PATCHES IN THIS VERSION
--------------------------------------------------------------------

1. readVibrationRMS(): per-axis mean removed, 3 axes combined
   (was |a| - 9.80665, which passed sensor offset through as "vibration").
2. DS18B20: 11-bit resolution (0.125 C steps, was 0.25 C).
3. DS18B20: non-blocking read (result of previous request is read each cycle).

--------------------------------------------------------------------
REAL HARDWARE
--------------------------------------------------------------------

MPU6050 / GY-521:
    VCC -> VIN / 5V
    GND -> GND
    SDA -> GPIO13
    SCL -> GPIO14

SH1106 OLED:
    VCC -> 3.3V
    GND -> GND
    SDA -> GPIO21
    SCL -> GPIO22

HC-SR04:
    VCC -> VIN / 5V
    GND -> GND
    TRIG -> GPIO5
    ECHO -> GPIO18 through 1k / 2k voltage divider

DS18B20:
    VCC -> 3.3V
    GND -> GND
    DATA -> GPIO19
    4.7k pull-up between DATA and 3.3V

--------------------------------------------------------------------
HALL SENSOR (SIMULATED CONTINUOUS READINGS)
--------------------------------------------------------------------

Continuous RPM and dynamic position tracking are derived internally 
via continuous virtual Hall pulse integration.

--------------------------------------------------------------------
PC COMMUNICATION
--------------------------------------------------------------------

ESP32 -> PC:

JSON telemetry at 115200 baud

PC -> ESP32:

@H=91,R=9,S=NORMAL,T=NONE

--------------------------------------------------------------------
OLED
--------------------------------------------------------------------

PAGE 1 -> STATUS
PAGE 2 -> SENSORS
PAGE 3 -> ACTION

Pages automatically rotate.

====================================================================
*/

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SH110X.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <math.h>

// =================================================================
// PIN DEFINITIONS
// =================================================================

// HC-SR04
#define TRIG_PIN 5
#define ECHO_PIN 18

// DS18B20
#define TEMP_PIN 19

// OLED
#define OLED_SDA 21
#define OLED_SCL 22

// MPU6050
#define MPU_SDA 13
#define MPU_SCL 14

// =================================================================
// I2C ADDRESSES
// =================================================================

#define OLED_ADDR 0x3C
#define MPU6050_ADDR 0x68

// =================================================================
// CONVEYOR CONFIGURATION
// =================================================================

const float ROLLER_DIAMETER_MM = 40.0;
const float BELT_LOOP_MM = 1100.0;

const int NUM_ZONES = 6;
const int NUM_BINS = 60;

// =================================================================
// CONTINUOUS HALL PULSE / RPM SIMULATION
// =================================================================

const float HALL_BASE_RPM = 62.0;
const float HALL_RPM_VARIATION = 1.5;
const unsigned long HALL_UPDATE_INTERVAL_MS = 10;

// =================================================================
// TIMING
// =================================================================

const unsigned long TELEMETRY_INTERVAL_MS = 600;
const unsigned long OLED_PAGE_INTERVAL_MS = 2300;
const unsigned long PC_TIMEOUT_MS = 4000;

// =================================================================
// I2C BUSES
// =================================================================

TwoWire I2C_OLED = TwoWire(0);
TwoWire I2C_MPU = TwoWire(1);

// =================================================================
// OLED
// =================================================================

Adafruit_SH1106G display(128, 64, &I2C_OLED, -1);
bool oledOK = false;
int oledPage = 0;
unsigned long lastOLEDChange = 0;

// =================================================================
// MPU6050
// =================================================================

bool mpuOK = false;

// =================================================================
// DS18B20
// =================================================================

OneWire oneWire(TEMP_PIN);
DallasTemperature ds18b20(&oneWire);
bool tempOK = false;

// =================================================================
// REAL SENSOR DATA
// =================================================================

float temperatureC = NAN;
float distanceCM = NAN;
float vibrationRMS = NAN;

// =================================================================
// CONTINUOUS HALL SENSOR & MOTION DATA
// =================================================================

float rpm = HALL_BASE_RPM;
float positionMM = 0.0;
int currentZone = 1;
int currentBin = 1;

float hallPhase = 0.0;
unsigned long lastHallUpdate = 0;
unsigned long lastPulseTime = 0;

// =================================================================
// PC / PYTHON FUSION
// =================================================================

int healthScore = 100;
int riskIndex = 0;
String systemState = "WAITING";
String topCause = "NONE";
unsigned long lastPCMessage = 0;

// =================================================================
// TELEMETRY
// =================================================================

unsigned long lastTelemetry = 0;

// =================================================================
// SAFE I2C DEVICE CHECK
// =================================================================

bool devicePresent(TwoWire &bus, uint8_t address)
{
  bus.beginTransmission(address);
  byte error = bus.endTransmission();
  return (error == 0);
}

// =================================================================
// INITIALIZE MPU6050
// =================================================================

bool initializeMPU()
{
  Serial.println("MPU6050: checking...");

  if (!devicePresent(I2C_MPU, MPU6050_ADDR))
  {
    Serial.println("MPU6050: NOT FOUND");
    return false;
  }

  Serial.println("MPU6050: FOUND");

  // Wake MPU6050
  I2C_MPU.beginTransmission(MPU6050_ADDR);
  I2C_MPU.write(0x6B);
  I2C_MPU.write(0x00);
  if (I2C_MPU.endTransmission(true) != 0)
  {
    Serial.println("MPU6050: WAKE FAILED");
    return false;
  }

  delay(100);

  // Accelerometer +/-2g
  I2C_MPU.beginTransmission(MPU6050_ADDR);
  I2C_MPU.write(0x1C);
  I2C_MPU.write(0x00);
  I2C_MPU.endTransmission(true);

  // Digital Low Pass Filter
  I2C_MPU.beginTransmission(MPU6050_ADDR);
  I2C_MPU.write(0x1A);
  I2C_MPU.write(0x03);
  I2C_MPU.endTransmission(true);

  Serial.println("MPU6050: READY");
  return true;
}

// =================================================================
// READ MPU6050 ACCELERATION
// =================================================================

bool readAcceleration(int16_t &ax, int16_t &ay, int16_t &az)
{
  if (!mpuOK)
  {
    return false;
  }

  I2C_MPU.beginTransmission(MPU6050_ADDR);
  I2C_MPU.write(0x3B);
  if (I2C_MPU.endTransmission(false) != 0)
  {
    return false;
  }

  int received = I2C_MPU.requestFrom((uint8_t)MPU6050_ADDR, (uint8_t)6, true);
  if (received != 6)
  {
    return false;
  }

  ax = ((int16_t)I2C_MPU.read() << 8) | I2C_MPU.read();
  ay = ((int16_t)I2C_MPU.read() << 8) | I2C_MPU.read();
  az = ((int16_t)I2C_MPU.read() << 8) | I2C_MPU.read();

  return true;
}

// =================================================================
// VIBRATION RMS  (PATCHED)
// AC RMS of the 3 axes combined. The per-axis average is removed, which
// cancels gravity, sensor tilt and sensor offset, leaving only shaking.
// =================================================================

float readVibrationRMS()
{
  if (!mpuOK)
  {
    return NAN;
  }

  const int SAMPLE_COUNT = 25;
  float xs[SAMPLE_COUNT], ys[SAMPLE_COUNT], zs[SAMPLE_COUNT];
  int n = 0;

  for (int i = 0; i < SAMPLE_COUNT; i++)
  {
    int16_t ax, ay, az;

    if (readAcceleration(ax, ay, az))
    {
      xs[n] = (ax / 16384.0f) * 9.80665f;
      ys[n] = (ay / 16384.0f) * 9.80665f;
      zs[n] = (az / 16384.0f) * 9.80665f;
      n++;
    }

    delay(4);
  }

  if (n < 5)
  {
    return NAN;
  }

  float mx = 0, my = 0, mz = 0;
  for (int i = 0; i < n; i++)
  {
    mx += xs[i];
    my += ys[i];
    mz += zs[i];
  }
  mx /= n;
  my /= n;
  mz /= n;

  float sumSq = 0.0f;
  for (int i = 0; i < n; i++)
  {
    float dx = xs[i] - mx;
    float dy = ys[i] - my;
    float dz = zs[i] - mz;
    sumSq += dx * dx + dy * dy + dz * dz;
  }

  return sqrt(sumSq / n);
}

// =================================================================
// HC-SR04
// =================================================================

float readDistanceCM()
{
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(3);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  unsigned long duration = pulseIn(ECHO_PIN, HIGH, 30000);
  if (duration == 0)
  {
    return NAN;
  }

  float distance = duration * 0.0343f / 2.0f;
  if (distance < 2.0f || distance > 400.0f)
  {
    return NAN;
  }

  return distance;
}

// =================================================================
// CALCULATE ZONE & BIN
// =================================================================

int calculateZone(float position)
{
  float zoneLength = BELT_LOOP_MM / NUM_ZONES;
  int zone = int(position / zoneLength) + 1;
  return constrain(zone, 1, NUM_ZONES);
}

int calculateBin(float position)
{
  float binLength = BELT_LOOP_MM / NUM_BINS;
  int bin = int(position / binLength) + 1;
  return constrain(bin, 1, NUM_BINS);
}

// =================================================================
// CONTINUOUS HALL SENSOR PULSE GENERATION & CALCULATION
// =================================================================

void updateHallSensor()
{
  unsigned long now = millis();
  if (now - lastHallUpdate < HALL_UPDATE_INTERVAL_MS)
  {
    return;
  }

  float deltaTime = (now - lastHallUpdate) / 1000.0f;
  lastHallUpdate = now;

  // Generate smooth target motor rotation dynamics
  hallPhase += deltaTime * 1.2f;
  float targetRPM = HALL_BASE_RPM + (HALL_RPM_VARIATION * sin(hallPhase));

  // Pulse interval based on target speed (1 pulse per revolution)
  float pulseIntervalUs = (60.0f / targetRPM) * 1000000.0f;

  // Calculate RPM strictly based on continuous simulated pulse intervals
  unsigned long nowUs = micros();
  if (lastPulseTime == 0) lastPulseTime = nowUs;

  if (nowUs - lastPulseTime >= pulseIntervalUs)
  {
    unsigned long deltaPulse = nowUs - lastPulseTime;
    rpm = (60.0f * 1000000.0f) / deltaPulse;
    lastPulseTime = nowUs;
  }

  // Update belt kinematics
  float rollerCircumferenceMM = PI * ROLLER_DIAMETER_MM;
  float beltSpeedMMPerSecond = (rollerCircumferenceMM * rpm) / 60.0f;

  positionMM += beltSpeedMMPerSecond * deltaTime;

  while (positionMM >= BELT_LOOP_MM) positionMM -= BELT_LOOP_MM;
  while (positionMM < 0) positionMM += BELT_LOOP_MM;

  currentZone = calculateZone(positionMM);
  currentBin = calculateBin(positionMM);
}

// =================================================================
// PC CONNECTION STATUS
// =================================================================

bool pcOnline()
{
  return (millis() - lastPCMessage < PC_TIMEOUT_MS);
}

// =================================================================
// READ PYTHON FEEDBACK
// =================================================================

void readPCFeedback()
{
  if (!Serial.available()) return;

  String line = Serial.readStringUntil('\n');
  line.trim();

  if (!line.startsWith("@H=")) return;

  int r = line.indexOf(",R=");
  int s = line.indexOf(",S=");
  int t = line.indexOf(",T=");

  if (r < 0 || s < 0 || t < 0) return;

  healthScore = constrain(line.substring(3, r).toInt(), 0, 100);
  riskIndex = constrain(line.substring(r + 3, s).toInt(), 0, 100);
  systemState = line.substring(s + 3, t);
  topCause = line.substring(t + 3);

  systemState.trim();
  topCause.trim();
  lastPCMessage = millis();
}

// =================================================================
// OLED DISPLAY HELPERS
// =================================================================

void oledHeader(const char *title)
{
  display.setTextColor(SH110X_WHITE);
  display.setTextSize(1);
  display.setCursor(0, 0);
  display.print("BRAVE|");
  display.println(title);
  display.drawLine(0, 10, 127, 10, SH110X_WHITE);
}

void oledFloat(float value, int decimals)
{
  if (isnan(value))
  {
    display.print("--");
  }
  else
  {
    display.print(value, decimals);
  }
}

// =================================================================
// OLED PAGES
// =================================================================

void showStatusScreen()
{
  oledHeader("STATUS");

  if (!pcOnline())
  {
    display.setCursor(0, 15);
    display.setTextSize(2);
    display.println("PC WAITING");

    display.setTextSize(1);
    display.setCursor(0, 39);
    display.print("MPU:");
    display.print(mpuOK ? "OK " : "OFF ");
    display.print("TMP:");
    display.println(tempOK ? "OK" : "OFF");

    display.setCursor(0, 52);
    display.print("Z");
    display.print(currentZone);
    display.print(" B");
    display.print(currentBin);
    display.print(" R");
    display.print(rpm, 0);
    return;
  }

  display.setCursor(0, 15);
  display.setTextSize(2);
  display.print("H");
  display.print(healthScore);
  display.print(" R");
  display.println(riskIndex);

  display.setTextSize(1);
  display.setCursor(0, 39);
  display.print("STATE:");
  display.println(systemState.substring(0, 12));

  display.setCursor(0, 52);
  display.print("Z");
  display.print(currentZone);
  display.print(" B");
  display.print(currentBin);
  display.print(" ");
  display.print(topCause.substring(0, 5));
}

void showSensorScreen()
{
  oledHeader("SENSORS");

  display.setCursor(0, 15);
  display.print("TEMP ");
  oledFloat(temperatureC, 1);
  display.print(" C");

  display.setCursor(0, 27);
  display.print("RPM ");
  display.print(rpm, 0);

  display.setCursor(0, 39);
  display.print("VIB ");
  oledFloat(vibrationRMS, 3);

  display.setCursor(0, 51);
  display.print("PROF ");
  oledFloat(distanceCM, 1);
  display.print(" B");
  display.print(currentBin);
}

void showActionScreen()
{
  oledHeader("ACTION");

  if (!pcOnline())
  {
    display.setCursor(0, 16);
    display.println("Fusion engine OFF");
    display.setCursor(0, 29);
    display.println("Sensors ON");
    display.setCursor(0, 42);
    display.println("Hall tracking ON");
    display.setCursor(0, 54);
    display.println("Start PC gateway");
    return;
  }

  display.setCursor(0, 15);
  display.print("CAUSE:");
  display.println(topCause.substring(0, 12));

  display.setCursor(0, 28);
  display.print("Z");
  display.print(currentZone);
  display.print(" BIN ");
  display.println(currentBin);

  display.setCursor(0, 41);
  if (systemState == "CRITICAL")
  {
    display.println("URGENT INSPECT");
    display.setCursor(0, 53);
    display.println("At safe stop");
  }
  else if (systemState == "WARNING")
  {
    display.println("INSPECT BELT");
    display.setCursor(0, 53);
    display.println("At safe stop");
  }
  else if (systemState == "EARLY")
  {
    display.println("WATCH TREND");
    display.setCursor(0, 53);
    display.println("Plan inspection");
  }
  else
  {
    display.println("MONITOR");
    display.setCursor(0, 53);
    display.println("Trend recording");
  }
}

void updateOLED()
{
  if (!oledOK) return;

  if (millis() - lastOLEDChange >= OLED_PAGE_INTERVAL_MS)
  {
    oledPage = (oledPage + 1) % 3;
    lastOLEDChange = millis();
  }

  display.clearDisplay();

  if (oledPage == 0) showStatusScreen();
  else if (oledPage == 1) showSensorScreen();
  else showActionScreen();

  display.display();
}

// =================================================================
// TELEMETRY
// =================================================================

void jsonFloat(float value, int decimals)
{
  if (isnan(value)) Serial.print("null");
  else Serial.print(value, decimals);
}

void sendJSON()
{
  Serial.print("{");
  Serial.print("\"time_ms\":");
  Serial.print(millis());

  Serial.print(",\"temperature_c\":");
  jsonFloat(temperatureC, 2);

  Serial.print(",\"distance_cm\":");
  jsonFloat(distanceCM, 2);

  Serial.print(",\"vibration_rms\":");
  jsonFloat(vibrationRMS, 4);

  Serial.print(",\"rpm\":");
  Serial.print(rpm, 2);

  Serial.print(",\"position_mm\":");
  Serial.print(positionMM, 2);

  Serial.print(",\"zone\":");
  Serial.print(currentZone);

  Serial.print(",\"bin\":");
  Serial.print(currentBin);

  Serial.print(",\"mpu6050_ok\":");
  Serial.print(mpuOK ? "true" : "false");

  Serial.print(",\"oled_ok\":");
  Serial.print(oledOK ? "true" : "false");

  Serial.print(",\"temp_ok\":");
  Serial.print(tempOK ? "true" : "false");

  Serial.print(",\"pc_online\":");
  Serial.print(pcOnline() ? "true" : "false");

  Serial.print(",\"health\":");
  Serial.print(healthScore);

  Serial.print(",\"risk\":");
  Serial.print(riskIndex);

  Serial.print(",\"state\":\"");
  Serial.print(systemState);
  Serial.print("\"");

  Serial.print(",\"cause\":\"");
  Serial.print(topCause);
  Serial.print("\"");

  Serial.println("}");
}

// =================================================================
// SETUP & LOOP
// =================================================================

void setup()
{
  Serial.begin(115200);
  Serial.setTimeout(20);
  delay(1500);

  Serial.println("\n========================================");
  Serial.println(" B.R.A.V.E. FINAL MASTER V7");
  Serial.println(" ESP32 SENSOR NODE");
  Serial.println("========================================");

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  digitalWrite(TRIG_PIN, LOW);
  Serial.println("GPIO: READY");

  I2C_OLED.begin(OLED_SDA, OLED_SCL, 100000);
  I2C_MPU.begin(MPU_SDA, MPU_SCL, 100000);
  delay(100);

  mpuOK = initializeMPU();

  ds18b20.begin();
  int deviceCount = ds18b20.getDeviceCount();
  if (deviceCount > 0)
  {
    tempOK = true;
    ds18b20.setResolution(11);            // 0.125 C steps (was 10-bit = 0.25 C)
    ds18b20.setWaitForConversion(false);  // don't block loop() while it converts
    ds18b20.requestTemperatures();        // start the first conversion
    Serial.println("DS18B20: READY");
  }
  else
  {
    tempOK = false;
    Serial.println("DS18B20: NOT FOUND");
  }

  oledOK = display.begin(OLED_ADDR, true);
  if (oledOK)
  {
    Serial.println("SH1106: READY");
    display.clearDisplay();
    display.setTextColor(SH110X_WHITE);

    display.setTextSize(1);
    display.setCursor(0, 0);
    display.println("B.R.A.V.E.");
    display.println("FINAL MASTER V7");
    display.drawLine(0, 18, 127, 18, SH110X_WHITE);

    display.setCursor(0, 23);
    display.print("MPU : ");
    display.println(mpuOK ? "ONLINE" : "OFFLINE");
    display.print("TEMP: ");
    display.println(tempOK ? "ONLINE" : "OFFLINE");
    display.println("HALL: ONLINE");
    display.println("3 PAGE UI READY");
    display.display();
  }

  rpm = HALL_BASE_RPM;
  positionMM = 0.0;
  currentZone = 1;
  currentBin = 1;
  lastHallUpdate = millis();

  lastOLEDChange = millis();
  lastTelemetry = millis();

  Serial.println("\n========================================");
  Serial.println(" BRAVE_READY");
  Serial.println("========================================");
  delay(1200);
}

void loop()
{
  readPCFeedback();
  updateHallSensor();
  updateOLED();

  if (millis() - lastTelemetry < TELEMETRY_INTERVAL_MS)
  {
    delay(2);
    return;
  }

  lastTelemetry = millis();

  if (tempOK)
  {
    // Read the conversion started on the previous cycle, then start the next one.
    float newTemperature = ds18b20.getTempCByIndex(0);
    ds18b20.requestTemperatures();

    if (newTemperature != DEVICE_DISCONNECTED_C &&
        newTemperature > -55.0f && newTemperature < 125.0f &&
        newTemperature != 85.0f)   // 85.0 = sensor power-on default, not a real reading
    {
      temperatureC = newTemperature;
    }
    else
    {
      temperatureC = NAN;
    }
  }
  else
  {
    temperatureC = NAN;
  }

  distanceCM = readDistanceCM();
  vibrationRMS = readVibrationRMS();

  sendJSON();
}
