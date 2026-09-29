"""Reads sensor readings from the ESP32 over USB serial and publishes them
for the dashboard to pick up.

Run this in its own terminal, separate from `streamlit run app.py`:

    python dashboard_gateway.py

It expects one JSON line per reading on serial, matching:

    {"vibration_rms": 0.74, "temperature_c": 41.2, "rpm": 81.5,
     "position_mm": 640, "mpu6050_ok": true, "temp_ok": true}

Any line that doesn't start with "{" is treated as ESP32 debug text and
just printed, not parsed.
"""

import csv
import json
import time
from pathlib import Path

import serial

from config import SERIAL_PORT, BAUD_RATE, STATE_FILE, CSV_FILE, RISK_WARNING, RISK_CRITICAL

CSV_COLUMNS = [
    "pc_time",
    "vibration_rms",
    "temperature_c",
    "rpm",
    "position_mm",
    "mpu6050_ok",
    "temp_ok",
]


def clamp(value, low, high):
    return max(low, min(high, value))


# ----------------------------------------------------------
# TEMPORARY fusion logic — proves the pipeline end-to-end.
# The 0.70 mm/s and 40.0 °C baselines are placeholders; replace
# them once you've calibrated against your own belt's normal range.
# ----------------------------------------------------------
def evaluate_state(data):
    vib = data.get("vibration_rms")
    temp = data.get("temperature_c")

    vib_score = 0.0
    temp_score = 0.0

    if vib is not None:
        vib_score = clamp((float(vib) - 0.70) * 30.0, 0, 50)

    if temp is not None:
        temp_score = clamp((float(temp) - 40.0) * 2.0, 0, 30)

    risk = int(round(clamp(vib_score + temp_score, 0, 100)))
    health = 100 - risk

    if risk >= RISK_CRITICAL:
        status = "CRITICAL"
    elif risk >= RISK_WARNING:
        status = "WARNING"
    else:
        status = "NORMAL"

    scores = {"VIBRATION": vib_score, "TEMPERATURE": temp_score}
    top_cause = max(scores, key=scores.get) if max(scores.values()) > 0 else "NONE"

    return health, risk, status, top_cause


def save_state(data, health, risk, status, top_cause):
    state = dict(data)
    state.update({
        "health_score": health,
        "risk_index": risk,
        "status": status,
        "top_cause": top_cause,
        "gateway_time": time.time(),
        "pc_time": time.time(),
        "connected": True,
    })
    Path(STATE_FILE).write_text(json.dumps(state, indent=2), encoding="utf-8")


def append_csv(data):
    path = Path(CSV_FILE)
    new_file = not path.exists()
    row = {"pc_time": time.time(), **{k: data.get(k) for k in CSV_COLUMNS if k != "pc_time"}}
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        if new_file:
            writer.writeheader()
        writer.writerow(row)


def main():
    print("=" * 60)
    print("B.R.A.V.E. EDGE GATEWAY")
    print("=" * 60)
    print(f"Port : {SERIAL_PORT}")
    print(f"Baud : {BAUD_RATE}")
    print()
    print("Close the Arduino Serial Monitor before running this.")
    print()

    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)
    print("ESP32 CONNECTED")
    print()

    try:
        while True:
            raw = ser.readline().decode("utf-8", errors="ignore").strip()
            if not raw:
                continue

            if not raw.startswith("{"):
                print("ESP32:", raw)
                continue

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                print("INVALID JSON:", raw)
                continue

            health, risk, status, top_cause = evaluate_state(data)
            save_state(data, health, risk, status, top_cause)
            append_csv(data)

            feedback = f"@H={health},R={risk},S={status},T={top_cause}\n"
            ser.write(feedback.encode("utf-8"))

            print(
                f"VIB {data.get('vibration_rms')} | "
                f"T {data.get('temperature_c')}C | "
                f"RPM {data.get('rpm')} | "
                f"POS {data.get('position_mm')}mm | "
                f"H {health} | R {risk} | {status}"
            )

    except KeyboardInterrupt:
        print("\nGateway stopped.")

    finally:
        ser.close()


if __name__ == "__main__":
    main()
