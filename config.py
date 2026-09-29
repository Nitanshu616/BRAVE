"""Hardware / domain constants shared across the app."""

# --- Serial gateway (real hardware path) ---
SERIAL_PORT = "COM6"
BAUD_RATE = 115200
STATE_FILE = "dashboard_state.json"
CSV_FILE = "brave_live.csv"
VISION_STATE_FILE = "vision_state.json"   # written by vision_gateway.py
VISION_MAX_AGE_S = 5.0                    # older than this -> treated as "no signal"

# --- Belt geometry ---
ROLLER_DIAMETER_MM = 40.0
BELT_LOOP_MM = 1100.0
PULSES_PER_REV = 4
NUM_ZONES = 6
NUM_BINS = 60
NUM_JOINTS = 6
NUM_SENSORS = 5  # MPU6050, DS18B20, Hall sensor, HC-SR04, ESP32 (connection) — the actual sensor rig
BELT_LENGTH_M = 1200  # 1.2 km, matches "Total Length" card in screenshots

# --- Fusion / risk thresholds (single source of truth) ---
WARNING_THRESHOLD = 70   # health % below this -> warning band on charts
CRITICAL_THRESHOLD = 35  # health % below this -> critical band on charts
RISK_WARNING = 35        # risk_index >= this -> WARNING
RISK_CRITICAL = 70       # risk_index >= this -> CRITICAL
ANOMALY_THRESHOLD = 0.70 # anomaly score (0-1) above this -> flagged

# --- Plant identity (header / sidebar chrome) ---
PLANT_NAME = "BRV-01"
PLANT_LOCATION = "Coal Handling Plant"
PLANT_SECTOR = "Plant: Sector A"
OPERATOR_NAME = "AK"
OPERATOR_ROLE = "Operator"