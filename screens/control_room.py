import streamlit as st

import config
from data import live_data
from ui import components as c
from ui import charts
from ui import theme as t
from ui.format import time_ago


def render():
    c.page_header("Control Room", "Real-time overview of conveyor belt health and system status",
                  right_html=c.flag_synced())

    state = live_data.get_live_state()
    joints = live_data.get_joints()
    predictive = live_data.get_predictive()
    alerts = live_data.get_alerts()

    joint_avg = round(sum(j["health"] for j in joints) / len(joints), 0)
    critical_zones = sum(1 for j in joints if j["status"] == "Critical")
    active_anomalies = sum(1 for j in joints if j["status"] != "Normal")

    cols = st.columns(4)
    with cols[0]:
        c.metric_card("heart", t.SAGE, "Overall Belt Health", f"{state['health_score']:.0f}", "%",
                      change="+2.4%", change_dir="up", good=True,
                      progress=state["health_score"], progress_color=t.GREEN)
    with cols[1]:
        c.metric_card("link", "#8A6A42", "Joint Health (Avg.)", f"{joint_avg:.0f}", "%",
                      change="-5.1%", change_dir="down", good=False,
                      progress=joint_avg, progress_color=t.AMBER)
    with cols[2]:
        c.metric_card("alert-triangle", t.RED, "Failure Risk", f"{state['risk_index']:.0f}", "%",
                      change="+8.3%", change_dir="up", good=False,
                      progress=state["risk_index"], progress_color=t.RED)
    with cols[3]:
        c.metric_card("clock", t.TAN, "Predicted RUL", f"{predictive['predicted_failure_days']}", "days",
                      change="+12%", change_dir="up", good=True,
                      progress=min(100, predictive["predicted_failure_days"] * 3), progress_color="#8A6A42")

    st.write("")
    left, right = st.columns([2, 1])
    with left:
        with st.container(border=True):
            c.section_start("Belt Health Trend", icon_name="bar-chart",
                            right_html=c.header_unit_select("Last 24 hours"))
            df = live_data.get_belt_health_trend()
            st.plotly_chart(charts.belt_health_trend(df), use_container_width=True,
                             config={"displayModeBar": False})
    with right:
        status_label = "OPERATIONAL" if state["status"] == "NORMAL" else state["status"].title()
        status_note = "System running normally" if state["status"] == "NORMAL" else "Attention required at active joint"
        fg, bg = t.status_colors("normal" if state["status"] == "NORMAL" else state["status"])
        inner = f"""
        <div style="background:{bg}; color:{fg}; text-align:center; font-weight:700; font-size:15px;
                    border-radius:10px; padding:10px; margin-bottom:8px; letter-spacing:0.4px;">{status_label}</div>
        <div style="text-align:center; color:var(--muted); font-size:13px; margin-bottom:10px;">{status_note}</div>
        <div class="brv-divider"></div>
        """ + c.kv_list([
            ("radio", "Active sensors", f"{config.NUM_SENSORS} / {config.NUM_SENSORS}", t.GREEN),
            ("alert-triangle", "Active anomalies", str(active_anomalies), t.AMBER),
            ("map-pin", "Critical zones", str(critical_zones), t.RED if critical_zones else t.GREEN),
            ("clock", "Last inspection", "08:42 AM", None),
        ])
        c.section("Current System State", inner, icon_name="building")

    left2, right2 = st.columns(2)
    with left2:
        items = []
        for a in alerts["alerts"][:3]:
            items.append({
                "severity": a["severity"],
                "title": a["message"],
                "meta": a["joint"],
                "time": time_ago(a["time"]),
            })
        c.section("Recent Alerts", c.alert_list(items), icon_name="clipboard",
                  right_html='<a class="brv-section-link" href="?page=alerts_actions" target="_self">View All →</a>')
    with right2:
        icon_map = {"High": "alert-triangle", "Medium": "clock", "Low": "check-circle"}
        items = []
        for m in predictive["schedule"][:3]:
            items.append({
                "icon": icon_map.get(m["priority"], "clock"),
                "title": f"{m['task']} ({m['joint']})",
                "priority": f"{m['priority']} Priority" if m["priority"] == "High" else m["priority"],
                "date": m["date"],
            })
        c.section("Maintenance Schedule", c.schedule_list(items), icon_name="calendar",
                  right_html='<a class="brv-section-link" href="?page=predictive_maintenance" target="_self">View All →</a>')
