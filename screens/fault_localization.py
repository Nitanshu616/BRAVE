import streamlit as st

from data import live_data
from ui import components as c
from ui import theme as t


def render():
    c.page_header("Fault Localization",
                  "Pinpointing the exact location and probable cause of conveyor belt abnormalities")

    fault = live_data.get_fault_location()
    joints = live_data.get_joints()

    cols = st.columns(4)
    with cols[0]:
        c.metric_card("target", t.RUST, "Fault Located At", str(fault["distance_m"]), "m",
                      caption=f"Joint {fault['joint']}")
    with cols[1]:
        c.metric_card("alert-triangle", t.RED, "Confidence Level", f"{fault['confidence_pct']:.0f}", "%",
                      caption="High confidence" if fault["confidence_pct"] >= 80 else "Moderate confidence")
    with cols[2]:
        c.metric_card("clock", "#8A6A42", "Detection Time", fault["time"].strftime("%H:%M:%S"), "",
                      caption=fault["time"].strftime("%d %b %Y"))
    with cols[3]:
        c.metric_card("wrench", t.SAGE, "Probable Cause", fault["cause"], "",
                      caption="Based on sensor patterns")

    st.write("")
    c.section("Joint Map", c.joint_map_html(joints, fault["joint"]), icon_name="map-pin",
              subtitle="Linear view of conveyor belt with joint locations", right_html=c.status_legend())

    left, right = st.columns([1.1, 1])
    with left:
        inner = c.kv_list([
            ("box", "Joint ID", fault["joint"], None),
            ("alert-triangle", "Distance from Head", f"{fault['distance_m']} m", None),
            ("map-pin", "Zone", fault["zone"], None),
            ("clock", "Detection Time", fault["time"].strftime("%d %b %Y, %H:%M:%S"), None),
            ("sliders", "Confidence Level", f"{fault['confidence_pct']:.0f}% (High)", t.RED),
            ("info", "Probable Cause", f"<b>{fault['cause']}</b>", None),
            ("radio", "Affected Sensors", c.chip_row(fault["affected_sensors"]), None),
            ("wrench", "Recommended Action", fault["action"], None),
        ])
        c.section("Fault Localization Details", inner, icon_name="map-pin",
                  right_html=c.pill("FAULT DETECTED", "critical", dot=False))
    with right:
        rows = [[r["parameter"], r["value"], r["range"], r["status"]] for r in live_data.get_joint_signature(fault["joint"])]
        c.section("Sensor Readings at " + fault["joint"], c.table_html(["Sensor", "Current Value", "Normal Range", "Status"],
                  rows, color_cols={3}), icon_name="radio")

    interpretation = (f"Elevated vibration, temperature and acoustic levels indicate possible {fault['cause'].lower()} "
                      f"at {fault['joint']}. Further physical inspection is recommended.")
    c.section("Interpretation", f'<div style="color:var(--ink); font-size:13.5px; line-height:1.6;">{interpretation}</div>',
              icon_name="info")
