"""Single data-access facade every screen imports from.

DEMO_MODE toggles between the synthetic simulator and the real ESP32
gateway path (dashboard_state.json / brave_live.csv written by a serial
bridge script, same contract as the BRAVE 2.0 gateway). Screens never
import data.simulator directly, so flipping this flag is the only change
needed to go live with real hardware.
"""

import json
import time
from pathlib import Path

import pandas as pd
from datetime import datetime
import config
from data import simulator

DEMO_MODE = False

_STATE_PATH = Path(config.STATE_FILE)
_CSV_PATH = Path(config.CSV_FILE)
_VISION_STATE_PATH = Path(config.VISION_STATE_FILE)


def _empty_state(data_source="No signal from gateway"):
    """Every key every screen expects, filled with safe placeholder values.
    Used whenever dashboard_state.json is missing, unreadable, or stale —
    so screens show '0%' / 'WAITING' instead of crashing with a KeyError."""
    return {
        "timestamp": datetime.now(),
        "connected": False,
        "demo_mode": False,
        "data_source": data_source,
        "mpu6050_ok": False,
        "temp_ok": False,
        "oled_ok": False,
        "vibration_mm_s": 0.0,
        "temperature_c": 0.0,
        "rpm": 0.0,
        "position_mm": 0.0,
        "trend_pct": {"vibration": 0.0, "temperature": 0.0, "rpm": 0.0, "position": 0.0},
        "health_score": 0,
        "risk_index": 0,
        "status": "WAITING",
        "top_cause": "NONE",
        "active_joint": "J-01",
        "active_zone": "Z-01",
    }


def _read_real_state(max_age_s=5.0):
    try:
        raw = json.loads(_STATE_PATH.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return _empty_state()

    age = time.time() - raw.get("gateway_time", 0)
    connected = age <= max_age_s
    if not connected:
        return _empty_state("Gateway offline")

    return {
        "timestamp": datetime.fromtimestamp(raw["pc_time"]) if raw.get("pc_time") else None,
        "connected": True,
        "demo_mode": False,
        "data_source": "ESP32 gateway",
        "mpu6050_ok": raw.get("mpu6050_ok", False),
        "temp_ok": raw.get("temp_ok", False),
        "oled_ok": raw.get("oled_ok", False),
        "vibration_mm_s": raw.get("vibration_rms", 0.0),
        "temperature_c": raw.get("temperature_c", 0.0),
        "rpm": raw.get("rpm", 0.0),
        "position_mm": raw.get("position_mm", 0.0),
        "trend_pct": {"vibration": 0.0, "temperature": 0.0, "rpm": 0.0, "position": 0.0},
        "health_score": raw.get("health_score", 0),
        "risk_index": raw.get("risk_index", 0),
        "status": raw.get("status", "WAITING"),
        "top_cause": raw.get("top_cause", "NONE"),
        "active_joint": f"J-{raw.get('zone', 1):02d}",
        "active_zone": f"Z-{raw.get('zone', 1):02d}",
    }


_LOG_PATH = Path("brave_log.jsonl")  # written by sensor_ai.py's mode_live, one JSON object per line
_HISTORY_COLUMNS = ["time", "vibration_mm_s", "temperature_c", "rpm", "position_mm"]


def _empty_history():
    return pd.DataFrame(columns=_HISTORY_COLUMNS)


def _read_real_history(rows=600):
    if not _LOG_PATH.exists():
        return _empty_history()

    records = []
    with _LOG_PATH.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue  # skip a half-written last line, if the file was mid-write

    if not records:
        return _empty_history()

    df = pd.DataFrame(records)
    df["time"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["vibration_mm_s"] = df.get("vibration_rms", 0.0)  # rename to match what screens/charts expect
    return df.tail(rows)


def _read_real_vision_state(max_age_s=None):
    max_age_s = max_age_s or config.VISION_MAX_AGE_S
    try:
        raw = json.loads(_VISION_STATE_PATH.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {"vision_connected": False, "damage_score": 0.0, "top_class": "NONE",
                "frame_jpeg_b64": None, "vision_time": None}

    age = time.time() - raw.get("gateway_time", 0)
    connected = age <= max_age_s
    return {
        "vision_connected": connected,
        "damage_score": raw.get("damage_score", 0.0) if connected else 0.0,
        "top_class": raw.get("top_class", "NONE") if connected else "NONE",
        "frame_jpeg_b64": raw.get("frame_jpeg_b64") if connected else None,
        "vision_time": datetime.fromtimestamp(raw["pc_time"]) if raw.get("pc_time") else None,
    }


def get_vision_state():
    """Vision-only counterpart to get_live_state(): frame + damage score.

    Kept separate from get_live_state() on purpose — vision_gateway.py and
    dashboard_gateway.py are independent processes writing independent
    files, so a stalled camera shouldn't make sensor cards look stale
    and vice versa.
    """
    if DEMO_MODE:
        return simulator.get_vision_state()
    return _read_real_vision_state()


def get_live_state():
    if DEMO_MODE:
        return simulator.get_live_state()
    return _read_real_state()


def get_history(minutes=60, points=60):
    if DEMO_MODE:
        return simulator.get_history(minutes=minutes, points=points)
    return _read_real_history()


def get_belt_health_trend(hours=24, points=48):
    return simulator.get_belt_health_trend(hours=hours, points=points)


def get_joints():
    return simulator.get_joints()


def get_joint_signature(joint_id=None):
    return simulator.get_joint_signature(joint_id)


def get_anomaly_trend(minutes=60, points=60):
    return simulator.get_anomaly_trend(minutes=minutes, points=points)


def get_current_anomaly():
    return simulator.get_current_anomaly()


def get_recent_anomalies():
    return simulator.get_recent_anomalies()


def get_fault_location():
    return simulator.get_fault_location()


def get_predictive():
    return simulator.get_predictive()


def get_alerts():
    return simulator.get_alerts()


def get_sensor_network():
    return simulator.get_sensor_network()


def get_live_stream(rows=6):
    return simulator.get_live_stream(rows=rows)