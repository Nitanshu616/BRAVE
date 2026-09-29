import streamlit as st
from streamlit_autorefresh import st_autorefresh

from ui.styles import load_css
from ui import components as c
from screens import splash, control_room, live_sensors, belt_digital_twin
from screens import anomaly_detection, fault_localization, predictive_maintenance, alerts_actions

st.set_page_config(page_title="B.R.A.V.E. | Belt Rupture Analysis & Vulnerability Estimation",
                    layout="wide", initial_sidebar_state="expanded")

load_css()

if not st.session_state.get("splash_shown", False):
    splash.show()
    st.stop()

if not st.session_state.get("paused", False):
    st_autorefresh(interval=2000, key="global_refresh")

SCREENS = {
    "control_room": control_room.render,
    "live_sensors": live_sensors.render,
    "belt_digital_twin": belt_digital_twin.render,
    "anomaly_detection": anomaly_detection.render,
    "fault_localization": fault_localization.render,
    "predictive_maintenance": predictive_maintenance.render,
    "alerts_actions": alerts_actions.render,
}

page = st.query_params.get("page", "control_room")
if page not in SCREENS:
    page = "control_room"

c.sidebar(page)
SCREENS[page]()
