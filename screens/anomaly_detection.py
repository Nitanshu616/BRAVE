import streamlit as st

import config
from data import live_data
from ui import components as c
from ui import charts
from ui import theme as t
from ui.icons import icon
from ui.format import fmt


def render():
    now_str = live_data.get_live_state()["timestamp"].strftime("%d %b %Y, %H:%M")
    c.page_header("Anomaly Detection", "AI-powered detection of abnormal patterns in conveyor belt joints",
                  right_html=c.date_range_pill(f"{now_str} – {now_str}"))

    state = live_data.get_live_state()
    joints = live_data.get_joints()
    current = live_data.get_current_anomaly()
    active_count = sum(1 for j in joints if j["status"] != "Normal")

    cols = st.columns(4)
    with cols[0]:
        c.metric_card("activity", t.SAGE, "Total Sensors Monitored", str(config.NUM_SENSORS), "",
                      caption="● All online", caption_color=t.GREEN)
    with cols[1]:
        c.metric_card("alert-triangle", t.RED, "Active Anomalies", str(max(active_count, 1)), "",
                      change=f"+{max(active_count,1)} in last hour", change_dir="up", good=False)
    with cols[2]:
        c.metric_card("clock", "#8A6A42", "Last Detected", current["time"].strftime("%H:%M:%S"), "",
                      caption=current["time"].strftime("%d %b %Y"))
    with cols[3]:
        c.metric_card("map-pin", t.SAGE, "Affected Joint", current["joint"], "",
                      caption=f"Zone {current['zone']}")

    st.write("")
    with st.container(border=True):
        head_l, head_r = st.columns([2.6, 1.2])
        with head_l:
            st.markdown(f'<div class="brv-section-title">{icon("bar-chart", 18)}Anomaly Score Trend</div>',
                        unsafe_allow_html=True)
            st.markdown('<div style="color:var(--muted); font-size:12.5px; margin:-4px 0 6px 0;">'
                        'Real-time anomaly score from key sensors at selected joint</div>', unsafe_allow_html=True)
        with head_r:
            st.markdown(f'<div style="padding-top:4px;">{c.header_unit_select(current["joint"])}</div>', unsafe_allow_html=True)
        df = live_data.get_anomaly_trend(minutes=60, points=60)
        st.plotly_chart(charts.anomaly_trend_chart(df), use_container_width=True, config={"displayModeBar": False})

    rows = [[current["joint"], current["zone"], current["time"].strftime("%d %b %Y, %H:%M:%S"),
             f"{current['score']:.2f}", current["severity"], current["type"], current["cause"], current["action"]]]
    inner = c.table_html(["Joint ID", "Zone", "Detection Time", "Anomaly Score", "Severity", "Type of Anomaly",
                          "Possible Cause", "Recommended Action"], rows, badge_cols={4}, bold_cols={0}) + \
        f'<div style="margin-top:14px; display:flex; align-items:center; gap:10px; font-size:13px; color:var(--muted);">' \
        f'<span style="font-weight:600; color:var(--ink);">Affected Sensors:</span>{c.chip_row(current["affected_sensors"])}</div>'
    c.section("Anomaly Details", inner, icon_name="clipboard",
              right_html=c.pill(f"{current['severity'].upper()} SEVERITY", current["severity"], dot=False))

    rows = []
    highlight = set()
    for i, a in enumerate(live_data.get_recent_anomalies()):
        if a["joint"] == current["joint"] and a["time"] == current["time"]:
            highlight.add(i)
        rows.append([a["time"].strftime("%H:%M:%S"), a["joint"], a["zone"], f"{a['score']:.2f}",
                    a["severity"], a["type"], a["status"]])
    c.section("Recent Anomalies", c.table_html(["Time", "Joint", "Zone", "Anomaly Score", "Severity", "Type", "Status"],
              rows, dot_cols={4}, color_cols={6}, bold_cols={1}, highlight_rows=highlight), icon_name="clipboard",
              right_html='<a class="brv-section-link" href="?page=anomaly_detection" target="_self">View All →</a>')

    sig_rows = [[r["parameter"], r["value"], r["range"], r["status"]] for r in live_data.get_joint_signature(current["joint"])]
    c.section(f"Sensor Readings at {current['joint']}", c.table_html(["Sensor", "Current Value", "Normal Range", "Status"],
              sig_rows, color_cols={3}), icon_name="radio", subtitle="At time of anomaly")
