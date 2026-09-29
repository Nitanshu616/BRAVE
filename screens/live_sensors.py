import streamlit as st

from data import live_data
from ui import components as c
from ui import charts
from ui import theme as t
from ui.icons import icon
from ui.format import fmt

RANGE_MINUTES = {"1H": 60, "6H": 360, "1D": 1440, "1W": 10080}

def render():
    state = live_data.get_live_state()

    vision = live_data.get_vision_state()
    c.camera_feed(
        frame_b64=vision["frame_jpeg_b64"],
        damage_score=vision["damage_score"],
        top_class=vision["top_class"],
        connected=vision["vision_connected"],
        timestamp_text=vision["vision_time"].strftime("%H:%M:%S") if vision["vision_time"] else "--",
    )
    st.write("")

    top_l, top_r = st.columns([3, 1.1])
    with top_l:
        c.render("""
        <div class="brv-page-title">Live Sensor Monitoring</div>
        <div class="brv-page-sub">Real-time edge telemetry from ESP32 sensor network</div>
        """)
    with top_r:
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        pill_col, btn_col = st.columns([2.2, 1])
        with pill_col:
            label = "ESP32 CONNECTED - BRV-01" if state["connected"] else "ESP32 DISCONNECTED"
            st.markdown(f'<div style="padding-top:6px;">{c.pill(label, "online" if state["connected"] else "offline")}</div>',
                        unsafe_allow_html=True)
        with btn_col:
            paused = st.session_state.get("paused", False)
            if st.button("▶ Resume" if paused else "⏸ Pause", key="pause_btn", use_container_width=True):
                st.session_state.paused = not paused

    cols = st.columns(4)
    hist = live_data.get_history(minutes=20, points=16)
    with cols[0]:
        c.sensor_card("activity", t.RED, "Vibration (RMS)", fmt(state["vibration_mm_s"], 2), "mm/s",
                      f"↑ {state['trend_pct']['vibration']}%", "up", False,
                      hist["vibration_mm_s"].tolist(), "MPU6050 - Structural Vibration")
    with cols[1]:
        c.sensor_card("thermometer", t.AMBER, "Temperature", fmt(state["temperature_c"], 1), "°C",
                      f"↑ {state['trend_pct']['temperature']}%", "up", False,
                      hist["temperature_c"].tolist(), "DS18B20 - Thermal Trend")
    with cols[2]:
        c.sensor_card("gauge", t.GREEN, "Roller Speed", fmt(state["rpm"], 1), "RPM",
                      f"↑ {state['trend_pct']['rpm']}%", "up", True,
                      hist["rpm"].tolist(), "Hall Sensor - Speed")
    with cols[3]:
        c.sensor_card("ruler", t.GREEN, "Belt Position", fmt(state["position_mm"], 0), "mm",
                      f"↑ {state['trend_pct']['position']}%", "up", True,
                      hist["position_mm"].tolist(), "HC-SR04 - Belt Profile")

    st.write("")
    left, right = st.columns([2, 1])
    with left:
        with st.container(border=True):
            head_l, head_r = st.columns([2.4, 1.6])
            with head_l:
                st.markdown(f'<div class="brv-section-title">{icon("activity", 18)}Live Telemetry</div>',
                            unsafe_allow_html=True)
            with head_r:
                range_choice = st.radio("range", list(RANGE_MINUTES.keys()), horizontal=True,
                                        label_visibility="collapsed", key="telemetry_range")
            minutes = RANGE_MINUTES[range_choice]
            df = live_data.get_history(minutes=minutes, points=60)
            st.plotly_chart(charts.telemetry_chart(df), use_container_width=True,
                             config={"displayModeBar": False})
    with right:
        inner = f'<div style="margin-bottom:10px;">{c.pill("Live", "online")}</div>' + c.kv_list([
            ("activity", "Vibration (RMS)", f"{fmt(state['vibration_mm_s'], 2)} mm/s", None),
            ("thermometer", "Temperature", f"{fmt(state['temperature_c'], 1)} °C", None),
            ("gauge", "Roller Speed", f"{fmt(state['rpm'], 1)} RPM", None),
            ("ruler", "Belt Position", f"{fmt(state['position_mm'], 0)} mm", None),
        ]) + f'<div class="brv-divider"></div><div style="font-size:11.5px; color:var(--muted);">Last updated: {state["timestamp"].strftime("%d %b %Y | %H:%M:%S") if state.get("timestamp") else "--"}</div>'
        c.section(f"Current Sensor Readings ({state['active_joint']})", inner, icon_name="calendar")

    bottom_l, bottom_r = st.columns([1.15, 1])
    with bottom_l:
        legend = (f'<div style="display:flex; gap:14px; font-size:12px; font-weight:600;">'
                  f'<span style="color:{t.GREEN};">● Online</span>'
                  f'<span style="color:{t.AMBER};">● Warning</span>'
                  f'<span style="color:{t.RED};">● Offline</span></div>')
        rows = [[r["id"], r["type"], r["location"], r["value"], r["status"]] for r in live_data.get_sensor_network()]
        c.section("Sensor Status", c.table_html(["Sensor", "Type", "Location", "Value", "Status"], rows, dot_cols={4}),
                  right_html=legend)
    with bottom_r:
        rows = [[r["time"], r["sensor"], r["parameter"], r["value"], r["status"]] for r in live_data.get_live_stream(5)]
        c.section("Live Data Stream", c.table_html(["Time", "Sensor", "Parameter", "Value", "Status"], rows, color_cols={4}),
                  right_html='<a class="brv-section-link" href="?page=live_sensors" target="_self">View All →</a>')