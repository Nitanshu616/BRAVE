import argparse, json, os, pickle, random, time
from collections import deque
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

RAW_FIELDS = [
    "temperature_c", "distance_cm", "vibration_rms",
    "rpm", "position_mm", "zone",
]
FEATURE_COLS = [
    "vib_mean", "vib_std", "dist_mean", "dist_std",
    "temp_slope",
    "rpm_mean", "rpm_std",
]

SAMPLE_INTERVAL_SEC = 1.0
WINDOW_SIZE = 10

MODEL_PATH = "isolation_forest.pkl"
BASELINE_CSV = "normal_baseline.csv"
LOG_JSONL = "brave_log.jsonl"
VISION_STATE = "vision_state.json"
STATE_FILE = "dashboard_state.json"  # what data/live_data.py in the dashboard reads

WEIGHTS = {"vision": 0.38, "vibration": 0.22, "ultrasonic": 0.20,
           "rpm": 0.12, "temperature": 0.08}  # sums to 1.00




#----------------Data Sources---------------

def synthetic_row(step, fault_type=None):
    vibration_rms = abs(random.gauss(0.12, 0.02))
    distance_cm = 14.0 + random.gauss(0, 0.15)
    temp_c = 30.0 + random.gauss(0, 0.05)
    rpm = 60.0 + random.gauss(0, 1.0)

    if fault_type == "vibration":
        vibration_rms += abs(random.gauss(0.35, 0.05))
    elif fault_type == "bump":
        distance_cm -= abs(random.gauss(2.5, 0.5))
    elif fault_type == "friction":
        temp_c += (step * SAMPLE_INTERVAL_SEC / 60) * 3
    elif fault_type == "slip":
        rpm -= abs(random.gauss(8, 2))

    position_mm = (step * 25) % 1200
    zone = int(position_mm // 200) + 1

    return {
        "temperature_c": round(temp_c, 2), "distance_cm": round(distance_cm, 2),
        "vibration_rms": round(vibration_rms, 3), "rpm": round(rpm, 1),
        "position_mm": round(position_mm, 1), "zone": zone,
    }

def synthetic_stream(duration_sec, fault_type=None, realtime=False):
    n = int(duration_sec / SAMPLE_INTERVAL_SEC)
    for step in range(n):
        yield synthetic_row(step, fault_type)
        if realtime:
            time.sleep(SAMPLE_INTERVAL_SEC)

def open_serial(port, baud):
    """Opens the serial port with a clear, actionable error if it fails --
    instead of a raw traceback that doesn't say what to actually check."""
    import serial
    try:
        ser = serial.Serial(port, baud, timeout=2)
        print(f"Connected to {port} at {baud} baud.")
        return ser
    except serial.SerialException as e:
        raise SystemExit(
            f"Could not open serial port '{port}': {e}\n"
            "Check: is the Arduino actually plugged in? Is the port name correct "
            "(Arduino IDE -> Tools -> Port)? Is Arduino IDE's Serial Monitor closed "
            "(only one program can hold the port open at a time)?"
        )

def serial_stream(port="COM6", baud=115200):
    import serial
    ser = open_serial(port, baud)
    while True:
        try:
            line = ser.readline().decode(errors="ignore").strip()
        except serial.SerialException:
            print(f"Lost connection to {port} -- reconnecting in 1s...")
            ser.close()
            time.sleep(1)
            ser = open_serial(port, baud)
            continue
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not all(k in row for k in RAW_FIELDS):
            continue  # malformed/incomplete row -- skip rather than crash
        if any(row[k] is None for k in RAW_FIELDS):
            continue  # firmware sends null when a sensor read fails (e.g. HC-SR04 timeout)
        yield {k: row[k] for k in RAW_FIELDS}




#-------------------Feature Extraction--------------
def extract_features(window_df: pd.DataFrame) -> dict:
    return {
        "vib_mean": float(window_df.vibration_rms.mean()),
        "vib_std": float(window_df.vibration_rms.std(ddof=0)),
        "dist_mean": float(window_df.distance_cm.mean()),
        "dist_std": float(window_df.distance_cm.std(ddof=0)),
        "temp_slope": float(window_df.temperature_c.iloc[-1] - window_df.temperature_c.iloc[0]),
        "rpm_mean": float(window_df.rpm.mean()),
        "rpm_std": float(window_df.rpm.std(ddof=0)),
    }

def windows_from_stream(row_stream):
    buf = deque(maxlen=WINDOW_SIZE)
    for row in row_stream:
        buf.append(row)
        if len(buf) == WINDOW_SIZE:
            yield extract_features(pd.DataFrame(buf)), buf[-1]


def time_boxed(stream, duration_sec):
    """Wraps any stream (synthetic or serial) and stops it after duration_sec
    of real wall-clock time. Lets collect_baseline/test run for a fixed
    window against REAL hardware, the same way they already do against
    synthetic data."""
    start = time.time()
    for row in stream:
        yield row
        if time.time() - start >= duration_sec:
            break


def get_stream(source, port, duration, fault_type=None):
    """One place that decides where readings come from, for every mode."""
    if source == "synthetic":
        return synthetic_stream(duration, fault_type=fault_type)
    return time_boxed(serial_stream(port), duration)



# ---------------- Isolation Forest ----------------
def train_iforest(baseline_csv: str = BASELINE_CSV):
    df = pd.read_csv(baseline_csv)
    model = IsolationForest(n_estimators=200, contamination=0.05, random_state=42)
    model.fit(df[FEATURE_COLS])
    return model




# ---------------- Vision score (written by vision_gateway.py) ----------------
def read_vision_score() -> float:
    if not os.path.exists(VISION_STATE):
        return 0.0
    try:
        with open(VISION_STATE) as f:
            # vision_gateway.py writes "damage_score" — not "vision_score".
            return float(json.load(f).get("damage_score", 0.0))
    except (json.JSONDecodeError, ValueError):
        return 0.0




# ---------------- Fusion ----------------
def fuse(vision_score: float, feats: dict):
    # Per-modality scores, 0-1. TUNE these divisors once you have real baseline stats.
    vibration = float(np.clip(feats["vib_mean"] / 0.3, 0, 1))
    ultrasonic = float(np.clip(feats["dist_std"] / 1.5, 0, 1))
    rpm = float(np.clip(abs(feats["rpm_mean"] - 60.0) / 15.0, 0, 1))
    temperature = float(np.clip(abs(feats["temp_slope"]) / 5.0, 0, 1))

    contributions = {
        "VISION": WEIGHTS["vision"] * vision_score,
        "VIBRATION": WEIGHTS["vibration"] * vibration,
        "ULTRASONIC": WEIGHTS["ultrasonic"] * ultrasonic,
        "RPM": WEIGHTS["rpm"] * rpm,
        "TEMPERATURE": WEIGHTS["temperature"] * temperature,
    }
    risk = sum(contributions.values())
    risk_index = round(float(np.clip(risk, 0, 1)) * 100)
    health_score = 100 - risk_index
    status = "CRITICAL" if risk_index > 70 else "WARNING" if risk_index > 35 else "NORMAL"
    top_cause = max(contributions, key=contributions.get) if risk_index > 0 else "NONE"
    return risk_index, health_score, status, top_cause




# ---------------- Modes ----------------
def mode_collect_baseline(duration, source="synthetic", port="COM6"):
    if source == "serial":
        print(f"Collecting {duration}s of REAL normal baseline from {port}.")
        print("Make sure the belt is running under completely normal conditions -- T0, no faults -- now.")
    else:
        print(f"Generating {duration}s of synthetic NORMAL data...")
    stream = get_stream(source, port, duration)
    rows = [feats for feats, _ in windows_from_stream(stream)]
    pd.DataFrame(rows).to_csv(BASELINE_CSV, index=False)
    print(f"Saved {len(rows)} feature windows to {BASELINE_CSV}")

def mode_train():
    model = train_iforest()
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    print(f"Trained Isolation Forest -> {MODEL_PATH}")

def mode_test(fault_type, duration, source="synthetic", port="COM6"):
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    if source == "serial":
        label = fault_type if fault_type else "NORMAL (no fault)"
        print(f"Collecting {duration}s of REAL data from {port}.")
        print(f"Physically trigger this condition on the rig now: {label}")
        stream = get_stream(source, port, duration)
    else:
        stream = get_stream(source, port, duration, fault_type=fault_type)
    rows = [feats for feats, _ in windows_from_stream(stream)]
    X = pd.DataFrame(rows)[FEATURE_COLS]
    scores = -model.score_samples(X)
    label = fault_type if fault_type else "NORMAL (no fault)"
    print(f"Fault type: {label}")
    print(f"Anomaly score  min={scores.min():.3f}  mean={scores.mean():.3f}  max={scores.max():.3f}")


# ---------------- Dashboard bridge ----------------
def _atomic_write_json(path, data, retries=10, base_delay=0.03):
    """Write JSON so the dashboard never reads a half-written file, and never
    crash if the dashboard has the file open (Windows raises PermissionError
    on os.replace in that case). Returns True on success, False if this
    update was skipped -- the next reading simply writes again."""
    tmp = f"{path}.{os.getpid()}.tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except OSError:
        return False

    try:
        for attempt in range(retries):
            try:
                os.replace(tmp, path)
                return True
            except PermissionError:
                time.sleep(base_delay * (attempt + 1))  # reader has it open; back off

        # Last resort: write in place (tiny file, partial read very unlikely)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f)
            return True
        except OSError:
            return False
    finally:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except OSError:
            pass

def save_dashboard_state(latest_row, vision_score, health_score, risk_index, status, top_cause):
    """Writes the same file dashboard_gateway.py writes, in the shape
    data/live_data.py's _read_real_state() expects. This is what actually
    gets the trained model's numbers onto the dashboard screens."""
    state = {
        "gateway_time": time.time(),
        "pc_time": time.time(),
        "connected": True,
        "mpu6050_ok": True,
        "temp_ok": True,
        "oled_ok": True,
        "vibration_rms": latest_row["vibration_rms"],
        "temperature_c": latest_row["temperature_c"],
        "rpm": latest_row["rpm"],
        "position_mm": latest_row["position_mm"],
        "zone": latest_row["zone"],
        "vision_score": round(vision_score, 3),
        "health_score": health_score,
        "risk_index": risk_index,
        "status": status,
        "top_cause": top_cause,
    }
    return _atomic_write_json(STATE_FILE, state)


def mode_live(source, port):
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    stream = synthetic_stream(10**9, realtime=True) if source == "synthetic" else serial_stream(port)

    with open(LOG_JSONL, "a") as log_file:
        for feats, latest_row in windows_from_stream(stream):
            vision_score = read_vision_score()
            risk_index, health_score, status, top_cause = fuse(vision_score, feats)
            record = {
                "timestamp": datetime.now().isoformat(), **latest_row,
                "vision_score": round(vision_score, 3),
                "health_score": health_score, "risk_index": risk_index,
                "status": status, "top_cause": top_cause,
            }
            log_file.write(json.dumps(record) + "\n")
            log_file.flush()
            try:
                if not save_dashboard_state(latest_row, vision_score, health_score, risk_index, status, top_cause):
                    print("[warn] dashboard state write skipped (file busy); will retry next reading")
            except Exception as e:  # never let a dashboard write stop the live run
                print(f"[warn] dashboard state write failed: {e}")
            print(record)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["collect_baseline", "train", "test", "live"], required=True)
    parser.add_argument("--fault", choices=["vibration", "bump", "friction", "slip"], default=None)
    parser.add_argument("--duration", type=int, default=90)
    parser.add_argument("--source", choices=["synthetic", "serial"], default="synthetic")
    parser.add_argument("--port", default="COM6")
    args = parser.parse_args()

    if args.mode == "collect_baseline":
        mode_collect_baseline(args.duration, args.source, args.port)
    elif args.mode == "train":
        mode_train()
    elif args.mode == "test":
        mode_test(args.fault, args.duration, args.source, args.port)
    elif args.mode == "live":
        try:
            mode_live(args.source, args.port)
        except KeyboardInterrupt:
            print("\nStopped by user.")