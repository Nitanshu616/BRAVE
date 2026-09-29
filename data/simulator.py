"""Synthetic telemetry engine for demo mode.

Every screen pulls from the functions in this module so that navigating
between screens shows one coherent scenario instead of independently
randomized numbers. The scenario is driven by a deterministic phase cycle
keyed off wall-clock time, so repeated calls within the same second agree,
and multiple screens rendered seconds apart still tell the same story
(a developing fault at the "active" joint).
"""

import base64
import io
import time
import math
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw

import config

CYCLE_S = 60.0          # full NORMAL -> WARNING -> CRITICAL -> recovery loop

# (id, zone, position_m, baseline health when not the currently-active joint)
JOINT_LAYOUT = [
    ("J-01", "Z-01", 0, 87),
    ("J-02", "Z-02", 200, 82),
    ("J-03", "Z-03", 400, 68),
    ("J-04", "Z-04", 600, 80),
    ("J-05", "Z-05", 842, 91),
    ("J-06", "Z-06", 1000, 76),
]


def _active_joint_info():
    """Which joint is currently developing the fault. Rotates to the next
    joint every CYCLE_S seconds so the highlighted joint on the joint map
    actually moves around instead of always being the same one."""
    idx = int(time.time() // CYCLE_S) % len(JOINT_LAYOUT)
    jid, zone, pos, _ = JOINT_LAYOUT[idx]
    return {"id": jid, "zone": zone, "position_m": pos}


def _phase():
    """Returns (status, risk_index 0-100, t_in_cycle 0-1) from wall clock."""
    t = time.time() % CYCLE_S
    frac = t / CYCLE_S
    # Smooth ramp up then down across the cycle (0 -> peak at 60% -> back to 0)
    ramp = math.sin(frac * math.pi) ** 1.4
    risk = 8 + ramp * 80  # 8..~88
    if risk >= config.RISK_CRITICAL:
        status = "CRITICAL"
    elif risk >= config.RISK_WARNING:
        status = "WARNING"
    else:
        status = "NORMAL"
    return status, risk, frac


def _seeded_rng(bucket_s=1):
    """RNG seeded to the current time bucket so a render pass is stable."""
    seed = int(time.time() // bucket_s)
    return random.Random(seed), np.random.default_rng(seed)


def get_live_state():
    status, risk, frac = _phase()
    rnd, rng = _seeded_rng()
    health = round(100 - risk, 1)
    active = _active_joint_info()

    vibration = round(2.0 + (risk / 100) * 11.5 + rnd.uniform(-0.3, 0.3), 2)
    temperature = round(28.0 + (risk / 100) * 44.0 + rnd.uniform(-0.4, 0.4), 1)
    rpm = round(78 + rnd.uniform(-2, 4) + (risk / 100) * 6, 1)
    position_mm = round((frac * config.BELT_LOOP_MM) % config.BELT_LOOP_MM, 0)

    top_cause = "NONE"
    if status != "NORMAL":
        top_cause = "VIBRATION" if vibration / 12 > temperature / 72 else "TEMPERATURE"

    return {
        "timestamp": datetime.now(),
        "connected": True,
        "demo_mode": True,
        "data_source": "Simulated (demo mode)",
        "mpu6050_ok": True,
        "temp_ok": True,
        "oled_ok": status != "CRITICAL",  # OLED drops out under sustained critical load
        "vibration_mm_s": vibration,
        "temperature_c": temperature,
        "rpm": rpm,
        "position_mm": position_mm,
        "trend_pct": {
            "vibration": round(6 + (risk / 100) * 14, 1),
            "temperature": round(2 + (risk / 100) * 6, 1),
            "rpm": round(rnd.uniform(0.1, 1.0), 1),
            "position": round(rnd.uniform(0.1, 0.6), 1),
        },
        "health_score": health,
        "risk_index": round(risk, 1),
        "status": status,
        "top_cause": top_cause,
        "active_joint": active["id"],
        "active_zone": active["zone"],
    }


_DEMO_FRAME_CACHE = {}


def get_vision_state():
    """Demo-mode stand-in for the real vision_gateway.py feed: a generated
    placeholder frame plus a damage score derived from the same risk phase
    driving every other card, so the story stays coherent across screens.
    """
    state = get_live_state()
    risk = state["risk_index"]
    rnd, _ = _seeded_rng()
    damage_score = round(min(0.97, max(0.02, risk / 100 * 0.9 + rnd.uniform(-0.05, 0.05))), 3)

    if state["status"] == "NORMAL":
        top_class = "NONE"
    elif state["status"] == "WARNING":
        top_class = "Small Tear"
    else:
        top_class = "Large Tear"

    # Regenerate the placeholder image only once a second (keyed off the
    # same time bucket as _seeded_rng) instead of every render.
    bucket = int(time.time())
    if _DEMO_FRAME_CACHE.get("bucket") != bucket:
        img = Image.new("RGB", (640, 360), (28, 26, 22))
        draw = ImageDraw.Draw(img)
        draw.rectangle([8, 8, 631, 351], outline=(150, 90, 60), width=2)
        draw.text((24, 24), "DEMO MODE — no live camera connected", fill=(230, 220, 200))
        draw.text((24, 48), f"Simulated damage score: {damage_score:.2f}", fill=(230, 220, 200))
        draw.text((24, 68), f"Simulated class: {top_class}", fill=(230, 220, 200))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=70)
        _DEMO_FRAME_CACHE["bucket"] = bucket
        _DEMO_FRAME_CACHE["frame_b64"] = base64.b64encode(buf.getvalue()).decode("utf-8")

    return {
        "vision_connected": True,
        "damage_score": damage_score,
        "top_class": top_class,
        "frame_jpeg_b64": _DEMO_FRAME_CACHE["frame_b64"],
        "vision_time": datetime.now(),
    }


def get_history(minutes=60, points=60):
    state = get_live_state()
    now = datetime.now()
    times = [now - timedelta(minutes=minutes) + timedelta(minutes=minutes * i / (points - 1))
             for i in range(points)]
    rnd, rng = _seeded_rng(bucket_s=1)
    ramp = np.linspace(0, 1, points) ** 1.3
    vib = 3.5 + ramp * (state["vibration_mm_s"] - 3.5) + rng.normal(0, 0.25, points)
    temp = 30 + ramp * (state["temperature_c"] - 30) + rng.normal(0, 0.3, points)
    rpm = 78 + rng.normal(0, 1.2, points) + ramp * 3
    position = np.linspace(0, state["position_mm"], points) % config.BELT_LOOP_MM
    return pd.DataFrame({
        "time": times,
        "vibration_mm_s": np.round(np.clip(vib, 0, None), 2),
        "temperature_c": np.round(temp, 1),
        "rpm": np.round(rpm, 1),
        "position_mm": np.round(position, 0),
    })


def get_belt_health_trend(hours=24, points=48):
    now = datetime.now()
    times = [now - timedelta(hours=hours) + timedelta(hours=hours * i / (points - 1))
             for i in range(points)]
    rng = np.random.default_rng(int(now.strftime("%Y%m%d")))
    base = 82 + rng.normal(0, 1.4, points).cumsum() * 0.05
    base = np.clip(base, 65, 92)
    state = get_live_state()
    tail = max(3, points // 8)
    taper = np.linspace(0, 1, tail) ** 1.5
    base[-tail:] = base[-tail] * (1 - taper) + state["health_score"] * taper
    return pd.DataFrame({"time": times, "health": np.round(base, 1)})


def get_joints():
    state = get_live_state()
    joints = []
    for i, (jid, zone, pos, baseline) in enumerate(JOINT_LAYOUT):
        h = state["health_score"] if jid == state["active_joint"] else baseline
        status = "Critical" if h < config.CRITICAL_THRESHOLD else ("Warning" if h < config.WARNING_THRESHOLD else "Normal")
        joints.append({
            "id": jid,
            "zone": zone,
            "position_m": pos,
            "health": round(h, 0),
            "status": status,
            "last_inspection": (datetime.now() - timedelta(days=i)).strftime("%d %b %Y"),
        })
    return joints


def get_joint_signature(joint_id=None):
    state = get_live_state()
    joint_id = joint_id or state["active_joint"]
    rnd, _ = _seeded_rng()
    tension = round(8 + (state["risk_index"] / 100) * 12 + rnd.uniform(-0.4, 0.4), 1)
    acoustic = round(45 + (state["risk_index"] / 100) * 50 + rnd.uniform(-1, 1), 1)
    readings = {
        "Vibration (mm/s)": (state["vibration_mm_s"], (0, 4.0)),
        "Temperature (°C)": (state["temperature_c"], (0, 50.0)),
        "Belt Tension (kN)": (tension, (8.0, 15.0)),
        "Acoustic Emission (dB)": (acoustic, (0, 70.0)),
    }
    joint_num = joint_id.split("-")[-1]
    rows = []
    for i, (label, (value, (lo, hi))) in enumerate(readings.items(), start=1):
        rows.append({
            "id": f"S-{joint_num}-{i}",
            "parameter": label,
            "value": value,
            "range": f"{lo:g} – {hi:g}",
            "status": "High" if value > hi else "Normal",
        })
    return rows


def get_anomaly_trend(minutes=60, points=60):
    state = get_live_state()
    now = datetime.now()
    times = [now - timedelta(minutes=minutes) + timedelta(minutes=minutes * i / (points - 1))
             for i in range(points)]
    rng = np.random.default_rng(int(now.timestamp() // 60))
    ramp = np.linspace(0, 1, points) ** 1.6
    peak = min(0.95, 0.25 + (state["risk_index"] / 100) * 0.7)
    vib = 0.15 + ramp * (peak - 0.15) + rng.normal(0, 0.02, points)
    temp = 0.10 + ramp * 0.25 + rng.normal(0, 0.015, points)
    tension = 0.08 + ramp * 0.18 + rng.normal(0, 0.012, points)
    acoustic = 0.05 + ramp * 0.15 + rng.normal(0, 0.01, points)
    return pd.DataFrame({
        "time": times,
        "Vibration": np.round(np.clip(vib, 0, 1), 3),
        "Temperature": np.round(np.clip(temp, 0, 1), 3),
        "Tension": np.round(np.clip(tension, 0, 1), 3),
        "Acoustic": np.round(np.clip(acoustic, 0, 1), 3),
    })


def get_current_anomaly():
    state = get_live_state()
    trend = get_anomaly_trend(minutes=5, points=5)
    score = float(trend["Vibration"].iloc[-1])
    severity = "High" if score >= config.ANOMALY_THRESHOLD else ("Medium" if score >= 0.5 else "Low")
    return {
        "joint": state["active_joint"],
        "zone": state["active_zone"],
        "time": state["timestamp"],
        "score": round(score, 2),
        "severity": severity,
        "type": "Abnormal vibration pattern",
        "cause": "Joint wear or misalignment",
        "affected_sensors": ["Vibration", "Temperature", "Acoustic"],
        "action": "Inspect joint and verify mechanical condition",
        "flagged": score >= config.ANOMALY_THRESHOLD,
    }


def get_recent_anomalies():
    current = get_current_anomaly()
    now = datetime.now()
    history = [
        {"time": now - timedelta(hours=2, minutes=17), "joint": "J-03", "zone": "Z-03", "score": 0.71,
         "severity": "Medium", "type": "Temperature deviation", "status": "Investigating"},
        {"time": now - timedelta(hours=4, minutes=44), "joint": "J-06", "zone": "Z-06", "score": 0.68,
         "severity": "Medium", "type": "Tension fluctuation", "status": "Resolved"},
        {"time": now - timedelta(hours=6, minutes=16), "joint": "J-02", "zone": "Z-02", "score": 0.77,
         "severity": "High", "type": "Acoustic spike", "status": "Resolved"},
        {"time": now - timedelta(hours=8, minutes=29), "joint": "J-04", "zone": "Z-04", "score": 0.66,
         "severity": "Medium", "type": "Irregular sensor pattern", "status": "Resolved"},
    ]
    rows = [{
        "time": current["time"], "joint": current["joint"], "zone": current["zone"],
        "score": current["score"], "severity": current["severity"], "type": current["type"],
        "status": "Open" if current["flagged"] else "Monitoring",
    }]
    rows.extend(history)
    return rows


def get_fault_location():
    state = get_live_state()
    active = _active_joint_info()
    rnd, _ = _seeded_rng()
    confidence = round(78 + (state["risk_index"] / 100) * 18 + rnd.uniform(-1, 1), 0)
    return {
        "distance_m": active["position_m"],
        "joint": state["active_joint"],
        "zone": state["active_zone"],
        "confidence_pct": min(99, confidence),
        "time": state["timestamp"],
        "cause": "Joint wear or misalignment",
        "affected_sensors": ["Vibration", "Temperature", "Acoustic"],
        "action": "Inspect joint, check alignment and schedule maintenance",
        "flagged": state["status"] != "NORMAL",
    }


def get_predictive():
    state = get_live_state()
    active_id = state["active_joint"]
    risk = state["risk_index"]
    days = max(2, round(30 - (risk / 100) * 24))
    prob = round(min(95, 20 + risk * 0.82), 0)
    urgency = "High" if risk >= config.RISK_CRITICAL else ("Medium" if risk >= config.RISK_WARNING else "Low")
    overall_health = round(100 - risk * 0.55, 0)

    month_start = pd.Timestamp(datetime.now()).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    months = pd.date_range(end=month_start, periods=5, freq="MS")
    actual = np.round(np.linspace(83, state["health_score"], 5), 1)
    future_months = pd.date_range(start=months[-1] + pd.DateOffset(months=1), periods=3, freq="MS")

    # predicted[0] anchors to the last actual point (index 4) so the dashed
    # line connects continuously where the solid "actual" line ends.
    predicted_future = np.round(np.linspace(actual[-1], max(15, actual[-1] - 35), 4), 1)
    band = np.linspace(0, 22, 4)
    upper = np.round(predicted_future + band, 1)
    lower = np.round(np.clip(predicted_future - band, 0, None), 1)

    forecast = pd.DataFrame({
        "month": list(months) + list(future_months),
        "actual": list(actual) + [np.nan] * 3,
        "predicted": [np.nan] * 4 + list(predicted_future),
        "upper": [np.nan] * 4 + list(upper),
        "lower": [np.nan] * 4 + list(lower),
    })

    fail_prob_by_joint = {"J-01": 8, "J-02": 15, "J-03": 28, "J-04": 20, "J-05": 18, "J-06": 20}
    fail_prob_by_joint[active_id] = int(prob)

    other_joints = [jid for jid, *_ in JOINT_LAYOUT if jid != active_id]
    schedule = [
        {"joint": active_id, "task": "Inspect & Realign", "priority": "High",
         "date": (datetime.now() + timedelta(days=days)).strftime("%d %b %Y"), "status": "Scheduled"},
        {"joint": other_joints[0], "task": "Check Tension", "priority": "Medium",
         "date": (datetime.now() + timedelta(days=days + 6)).strftime("%d %b %Y"), "status": "Planned"},
        {"joint": other_joints[1], "task": "Routine Inspection", "priority": "Low",
         "date": (datetime.now() + timedelta(days=days + 14)).strftime("%d %b %Y"), "status": "Planned"},
        {"joint": other_joints[2], "task": "Sensor Calibration", "priority": "Low",
         "date": (datetime.now() + timedelta(days=days + 21)).strftime("%d %b %Y"), "status": "Planned"},
    ]

    component_health = {
        "Belt Tension": max(30, round(88 - risk * 0.42, 0)),
        "Roller Condition": max(40, round(90 - risk * 0.28, 0)),
        "Splice Integrity": max(25, round(85 - risk * 0.47, 0)),
        "Idler Alignment": max(35, round(89 - risk * 0.35, 0)),
    }

    return {
        "predicted_failure_days": days,
        "predicted_failure_date": (datetime.now() + timedelta(days=days)).strftime("%d %b %Y"),
        "failure_probability_pct": prob,
        "urgency": urgency,
        "overall_health_pct": overall_health,
        "scheduled_count": len(schedule),
        "forecast": forecast,
        "fail_prob_by_joint": fail_prob_by_joint,
        "schedule": schedule,
        "component_health": component_health,
        "active_joint": state["active_joint"],
    }


def get_alerts():
    state = get_live_state()
    active = _active_joint_info()
    now = datetime.now()
    dynamic_severity = "Critical" if state["status"] == "CRITICAL" else ("Warning" if state["status"] == "WARNING" else "Info")
    dynamic = {
        "time": now, "severity": dynamic_severity, "joint": state["active_joint"],
        "parameter": "Vibration",
        "message": f"High vibration detected at {state['active_joint']} ({state['vibration_mm_s']} mm/s).",
        "status": "Open" if dynamic_severity != "Info" else "Resolved",
        "threshold": "> 8.0 mm/s",
        "value_text": f"Vibration ({state['vibration_mm_s']} mm/s)",
        "location_text": f"Joint {state['active_joint']} ({active['position_m']} m from head)",
        "suggested_action": "Inspect joint, check alignment and schedule maintenance.",
    }
    history = [
        {"time": now - timedelta(minutes=43), "severity": "Warning", "joint": "J-04", "parameter": "Temperature",
         "message": "Elevated temperature (68.5 °C)", "status": "Acknowledged"},
        {"time": now - timedelta(hours=2, minutes=14), "severity": "Critical", "joint": "J-05", "parameter": "Acoustic",
         "message": "Abnormal acoustic emission (92.1 dB)", "status": "Open"},
        {"time": now - timedelta(hours=3, minutes=29), "severity": "Warning", "joint": "J-03", "parameter": "Belt Tension",
         "message": "Tension above threshold (18.2 kN)", "status": "Acknowledged"},
        {"time": now - timedelta(hours=5, minutes=37), "severity": "Info", "joint": "J-02", "parameter": "Status",
         "message": "Sensor reconnected", "status": "Resolved"},
        {"time": now - timedelta(hours=6, minutes=50), "severity": "Warning", "joint": "J-04", "parameter": "Rollers",
         "message": "Unusual roller vibration", "status": "Resolved"},
    ]
    all_alerts = [dynamic] + history
    critical_count = sum(1 for a in all_alerts if a["severity"] == "Critical")
    warning_count = sum(1 for a in all_alerts if a["severity"] == "Warning")
    pending = sum(1 for a in all_alerts if a["status"] == "Open")

    days = pd.date_range(end=datetime.now(), periods=7, freq="D")
    rng = np.random.default_rng(int(now.strftime("%Y%m%d")))
    trend = pd.DataFrame({
        "day": days,
        "Critical": rng.integers(1, 6, 7),
        "Warning": rng.integers(2, 7, 7),
        "Info": rng.integers(1, 4, 7),
    })
    trend.loc[trend.index[-1], ["Critical", "Warning", "Info"]] = [
        critical_count, warning_count, len(all_alerts) - critical_count - warning_count
    ]

    return {
        "alerts": all_alerts,
        "detail": dynamic,
        "counts": {
            "critical": critical_count,
            "warning": warning_count,
            "total_24h": len(all_alerts),
            "pending": pending,
        },
        "trend": trend,
        "system_status": {
            "sensors": f"{config.NUM_SENSORS} / {config.NUM_SENSORS}", "sensors_state": "Online",
            "communication": "Stable", "packet_loss": "0% Packet Loss",
            "data_processing": "Running", "data_state": "Normal",
            "alert_engine": "Active", "alert_state": "Monitoring 24/7",
        },
    }


def get_sensor_network():
    state = get_live_state()
    rows = [
        {"id": "S-01", "type": "Vibration (MPU6050)", "location": config.PLANT_NAME,
         "value": f"{state['vibration_mm_s']:.2f} mm/s",
         "status": "Online" if state["mpu6050_ok"] else "Offline"},
        {"id": "S-02", "type": "Temperature (DS18B20)", "location": config.PLANT_NAME,
         "value": f"{state['temperature_c']:.1f} °C",
         "status": "Online" if state["temp_ok"] else "Offline"},
        {"id": "S-03", "type": "Roller Speed (Hall)", "location": config.PLANT_NAME,
         "value": f"{state['rpm']:.1f} RPM", "status": "Online"},
        {"id": "S-04", "type": "Belt Position (HC-SR04)", "location": config.PLANT_NAME,
         "value": f"{state['position_mm']:.0f} mm",
         "status": "Online" if state["oled_ok"] else "Offline"},
        {"id": "S-05", "type": "ESP32 (connection)", "location": config.PLANT_NAME,
         "value": "Connected" if state["connected"] else "Disconnected",
         "status": "Online" if state["connected"] else "Offline"},
    ]
    return rows


def get_live_stream(rows=5):
    state = get_live_state()
    now = datetime.now()
    entries = [
        ("Vibration", f"{state['vibration_mm_s']} mm/s", "Normal" if state["status"] == "NORMAL" else "Warning"),
        ("Temperature", f"{state['temperature_c']} °C", "Normal"),
        ("Roller Speed", f"{state['rpm']} RPM", "Normal"),
        ("Belt Position", f"{state['position_mm']:.0f} mm", "Normal"),
        ("Connection", "ESP32 connected" if state["connected"] else "ESP32 disconnected",
         "Normal" if state["connected"] else "Warning"),
    ]
    out = []
    for i, (param, value, status) in enumerate(entries[:rows]):
        out.append({
            "time": (now - timedelta(seconds=i * 4)).strftime("%H:%M:%S"),
            "sensor": f"S-{(i % len(entries)) + 1:02d}",
            "parameter": param,
            "value": value,
            "status": status,
        })
    return out