import streamlit as st

import config
from data import live_data
from ui import components as c
from ui import theme as t
from ui.format import fmt


def render():
    c.page_header("Belt Digital Twin", "Live digital representation of conveyor belt BRV-01")

    state = live_data.get_live_state()
    joints = live_data.get_joints()
    active = next(j for j in joints if j["id"] == state["active_joint"])

    cols = st.columns(4)
    with cols[0]:
        c.metric_card("link", "#8A6A42", "Total Length", f"{config.BELT_LENGTH_M / 1000:.1f}", "km",
                      caption=config.PLANT_NAME)
    with cols[1]:
        c.metric_card("box", t.SAGE, "Monitored Joints", str(len(joints)), "",
                      caption=f"J-01 to J-{len(joints):02d}")
    with cols[2]:
        c.metric_card("radio", t.GREEN, "Active Sensors", f"{config.NUM_SENSORS} / {config.NUM_SENSORS}", "",
                      caption="● All online", caption_color=t.GREEN)
    with cols[3]:
        c.metric_card("heart", t.SAGE, "Belt Health", f"{state['health_score']:.0f}", "%",
                      change="+2.4%", change_dir="up", good=True,
                      caption="Healthy operating condition" if state["health_score"] >= config.WARNING_THRESHOLD else "Needs attention")

    st.write("")
    c.section("Joint Map", c.joint_map_html(joints, state["active_joint"]), icon_name="map-pin",
              subtitle="Linear view of conveyor belt with joint locations",
              right_html=c.status_legend())

    left, right = st.columns([1.25, 1])
    with left:
        rows = [[j["id"], j["status"], f"{j['health']:.0f}%", j["last_inspection"]] for j in joints]
        highlight = {i for i, j in enumerate(joints) if j["id"] == state["active_joint"]}
        c.section("Joint Health Status", c.table_html(["Joint", "Status", "Health (%)", "Last Inspection"],
                  rows, dot_cols={1}, bold_cols={0}, highlight_rows=highlight), icon_name="clipboard")
    with right:
        fg, bg = t.status_colors(active["status"])
        badge = c.pill(active["status"].upper(), active["status"], dot=False)
        inner = c.kv_list([
            ("map-pin", "Location", f"{active['position_m']} m", None),
            ("building", "Zone", active["zone"], None),
            ("wrench", "Joint Type", "Return Roller", None),
            ("calendar", "Installation Date", "12 Mar 2023", None),
            ("clock", "Last Inspection", active["last_inspection"], None),
            ("activity", "Health Status", f"{active['status']} ({active['health']:.0f}%)", fg),
        ])
        c.section(f"Joint Details – {active['id']}", inner, icon_name="building", right_html=badge)

    rows = []
    for r in live_data.get_joint_signature(state["active_joint"]):
        rows.append([r["id"], r["parameter"], r["value"], r["range"], r["status"]])
    c.section(f"Sensor Data at {active['id']}",
              c.table_html(["Sensor ID", "Parameter", "Current Value", "Normal Range", "Status"], rows, color_cols={4}, bold_cols={0}),
              icon_name="radio", subtitle="Real-time sensor readings at the fault location")
