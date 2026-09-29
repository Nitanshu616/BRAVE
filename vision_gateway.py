"""Runs the trained YOLO vision model on the live camera feed and publishes
annotated frames + damage scores for the Streamlit dashboard to show inline.

Run this in its own terminal, alongside `streamlit run app.py` and (if you're
using it) `dashboard_gateway.py` — they write to different state files
(vision_state.json vs dashboard_state.json) so they don't collide:

    python vision_gateway.py

Deliberately does NOT call cv2.imshow(). The dashboard is the viewer: this
script just writes the annotated JPEG (as base64) into vision_state.json,
and the Streamlit app renders it with st.image on its normal autorefresh.
"""

import base64
import json
import time
from pathlib import Path

import cv2
from ultralytics import YOLO

from config import VISION_STATE_FILE

MODEL_PATH = "best_v3.pt"        # the corrected, non-leaky model — NOT best.pt
CAMERA_INDEX = 2                  # change if your USB/UVC camera isn't index 0
CONF_THRESHOLD = 0.35
JPEG_QUALITY = 60                 # keep the base64 payload small so writes stay fast
FRAME_WIDTH = 640                 # resize before encoding
WRITE_INTERVAL_S = 0.3            # ~3 fps is plenty; dashboard refreshes every 2s anyway

# Belt Joint is a landmark, not damage — excluded from the score, same
# convention as brave_live_vision.py's damage_score.
DAMAGE_CLASSES = {"Large Hole", "Large Tear", "Small Hole", "Small Tear"}
BOX_COLOR_DAMAGE = (53, 65, 190)   # BGR
BOX_COLOR_JOINT = (190, 130, 53)   # BGR


def draw_and_score(frame, result):
    damage_score = 0.0
    top_class = "NONE"
    boxes = result.boxes
    names = result.names

    if boxes is not None:
        for box in boxes:
            cls_id = int(box.cls[0])
            label = names[cls_id]
            conf = float(box.conf[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            color = BOX_COLOR_JOINT if label == "Belt Joint" else BOX_COLOR_DAMAGE
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, f"{label} {conf:.2f}", (x1, max(0, y1 - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            if label in DAMAGE_CLASSES and conf > damage_score:
                damage_score = conf
                top_class = label

    return frame, damage_score, top_class


def encode_frame(frame):
    h, w = frame.shape[:2]
    if w > FRAME_WIDTH:
        scale = FRAME_WIDTH / w
        frame = cv2.resize(frame, (FRAME_WIDTH, int(h * scale)))
    ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    return base64.b64encode(buf).decode("utf-8") if ok else None


def save_state(frame_b64, damage_score, top_class, connected):
    state = {
        "gateway_time": time.time(),
        "pc_time": time.time(),
        "connected": connected,
        "damage_score": round(damage_score, 3),
        "top_class": top_class,
        "frame_jpeg_b64": frame_b64,
    }
    # write-then-rename so the dashboard never reads a half-written file
    tmp = Path(VISION_STATE_FILE + ".tmp")
    for attempt in range(4):
        try:
            tmp.write_text(json.dumps(state), encoding="utf-8")
            tmp.replace(VISION_STATE_FILE)
            return
        except PermissionError as e:
            # On Windows this is almost always transient: antivirus, OneDrive/
            # cloud sync, or another program briefly locking the file. Retry a
            # few times instead of killing the whole camera loop over one write.
            if attempt == 3:
                print(f"WARNING: could not update {VISION_STATE_FILE} after several tries ({e}). "
                      f"Dashboard will show the last good frame until this clears up.")
            else:
                time.sleep(0.15)


def main():
    print("=" * 60)
    print("B.R.A.V.E. VISION GATEWAY")
    print("=" * 60)
    print(f"Model  : {MODEL_PATH}")
    print(f"Camera : index {CAMERA_INDEX}")
    print(f"Writing: {VISION_STATE_FILE}")
    print()

    model = YOLO(MODEL_PATH)
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open camera index {CAMERA_INDEX}")

    last_write = 0.0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("Frame grab failed, retrying...")
                time.sleep(0.5)
                continue

            result = model.predict(frame, conf=CONF_THRESHOLD, verbose=False)[0]
            annotated, damage_score, top_class = draw_and_score(frame.copy(), result)

            now = time.time()
            if now - last_write >= WRITE_INTERVAL_S:
                frame_b64 = encode_frame(annotated)
                save_state(frame_b64, damage_score, top_class, connected=True)
                last_write = now
                print(f"damage_score={damage_score:.3f}  class={top_class}")

    except KeyboardInterrupt:
        print("\nVision gateway stopped.")
    finally:
        cap.release()


if __name__ == "__main__":
    main()