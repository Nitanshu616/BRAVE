from datetime import datetime, timedelta

import streamlit as st

from data import live_data
from ui import components as c
from ui import charts
from ui import theme as t
from ui.icons import icon


def render():
    right = ('<div style="display:flex; gap:10px; font-size:12px; font-weight:700; letter-spacing:1px; '
             'color:var(--muted); text-transform:uppercase;"><span>Detect</span><span>|</span>'
             '<span>Predict</span><span>|</span><span>Prevent</span></div>')
    c.page_header("Alerts & Actions",
                  "Real-time notifications and recommended actions for a safer and smoother operation",
                  right_html=right)

    data = live_data.get_alerts()
    counts = dict(data["counts"])
    detail = data["detail"]
    acknowledged = st.session_state.get("acknowledged_joint") == detail["joint"]
    if acknowledged:
        counts["pending"] = max(0, counts["pending"] - 1)

    trend = data["trend"]
    daily_totals = trend[["Critical", "Warning", "Info"]].sum(axis=1)
    today_total, yesterday_total = int(daily_totals.iloc[-1]), int(daily_totals.iloc[-2])
    pct_change = round((today_total - yesterday_total) / yesterday_total * 100) if yesterday_total else 0

    cols = st.columns(4)
    with cols[0]:
        c.metric_card("bell", t.RED, "Critical Alerts", str(counts["critical"]), "",
                      caption="Requires immediate action", caption_color=t.RED)
    with cols[1]:
        c.metric_card("bell", t.AMBER, "Warning Alerts", str(counts["warning"]), "",
                      caption="Monitor closely", caption_color=t.AMBER)
    with cols[2]:
        c.metric_card("bell", "#8A8171", "Total Alerts (24h)", str(counts["total_24h"]), "",
                      change=f"{pct_change:+d}% from previous day",
                      change_dir="down" if pct_change <= 0 else "up", good=pct_change <= 0)
    with cols[3]:
        c.metric_card("clock", "#8A6A42", "Pending Actions", str(counts["pending"]), "",
                      caption="Need confirmation")

    st.write("")
    left, right_col = st.columns([1.3, 1])
    with left:
        rows = []
        for i, a in enumerate(data["alerts"][:6]):
            status = "Acknowledged" if (i == 0 and acknowledged and a["status"] == "Open") else a["status"]
            rows.append([a["time"].strftime("%H:%M:%S"), a["severity"], a["joint"], a["parameter"],
                        a["message"], status])
        c.section("Recent Alerts", c.table_html(["Time", "Severity", "Location / Joint", "Parameter", "Message", "Status"],
                  rows, badge_cols={1}, color_cols={5}, bold_cols={2}), icon_name="bell",
                  right_html='<a class="brv-section-link" href="?page=alerts_actions" target="_self">View All →</a>')
    with right_col:
        status_text = "Acknowledged" if acknowledged else detail["status"]
        inner = c.kv_list([
            ("clock", "Time", detail["time"].strftime("%d %b %Y, %H:%M:%S"), None),
            ("map-pin", "Location", detail["location_text"], None),
            ("activity", "Parameter", detail["value_text"], None),
            ("alert-triangle", "Threshold", detail["threshold"], None),
            ("info", "Message", detail["message"], None),
            ("wrench", "Suggested Action", detail["suggested_action"], None),
            ("check-circle", "Status", status_text, t.GREEN if acknowledged else None),
        ])
        with st.container(border=True):
            c.render(f"""
            <div class="brv-section-head">
                <div class="brv-section-title">Alert Details</div>
                <div>{c.pill(detail['severity'].upper(), detail['severity'], dot=False)}</div>
            </div>
            {inner}
            """)
            b1, b2 = st.columns(2)
            with b1:
                if acknowledged:
                    st.success("Acknowledged", icon="✅")
                elif st.button("✓ Acknowledge", use_container_width=True, key="ack_btn"):
                    st.session_state.acknowledged_joint = detail["joint"]
                    st.rerun()

                inspection_scheduled = st.session_state.get("inspection_joint") == detail["joint"]
                if inspection_scheduled:
                    st.success(f"Inspection {st.session_state.inspection_date}", icon="📅")
                elif st.button("📅 Schedule Inspection", use_container_width=True, key="sched_btn"):
                    st.session_state.inspection_joint = detail["joint"]
                    st.session_state.inspection_date = (datetime.now() + timedelta(days=1)).strftime("%d %b")
                    st.rerun()
            with b2:
                work_order_created = st.session_state.get("work_order_joint") == detail["joint"]
                if work_order_created:
                    st.success(st.session_state.work_order_id, icon="🔧")
                elif st.button("🔧 Create Work Order", use_container_width=True, key="wo_btn"):
                    st.session_state.work_order_joint = detail["joint"]
                    st.session_state.work_order_id = f"WO-{datetime.now().strftime('%H%M%S')}"
                    st.rerun()

                if st.button("📈 View Trends", use_container_width=True, key="trend_btn"):
                    st.query_params["page"] = "anomaly_detection"
                    st.rerun()

    left2, right2 = st.columns([1.3, 1])
    with left2:
        with st.container(border=True):
            head_l, head_r = st.columns([2, 1.4])
            with head_l:
                c.section_start("Alert Trends (Last 7 Days)", icon_name="bar-chart")
            with head_r:
                st.markdown(f'<div style="padding-top:6px;">{c.chart_legend([("Critical", t.RED, "solid"), ("Warning", t.AMBER, "solid"), ("Info", "#9AA3B5", "solid")])}</div>',
                            unsafe_allow_html=True)
            st.plotly_chart(charts.alert_trend_chart(data["trend"]), use_container_width=True,
                             config={"displayModeBar": False})
    with right2:
        sys = data["system_status"]
        cards = [
            {"icon": "radio", "title": "Sensors", "status": sys["sensors_state"], "color": t.GREEN, "subtitle": sys["sensors"]},
            {"icon": "wifi", "title": "Communication", "status": sys["communication"], "color": t.GREEN, "subtitle": sys["packet_loss"]},
            {"icon": "database", "title": "Data Processing", "status": sys["data_processing"], "color": t.GREEN, "subtitle": sys["data_state"]},
            {"icon": "bell", "title": "Alert Engine", "status": sys["alert_engine"], "color": t.GREEN, "subtitle": sys["alert_state"]},
        ]
        c.section("System Status", c.mini_grid(cards), icon_name="sliders",
                  right_html=c.pill("All Systems Operational", "normal", dot=True))

    c.render(f"""
    <div style="display:flex; justify-content:space-between; align-items:center; color:var(--muted); font-size:12.5px; padding:6px 4px;">
        <div style="display:flex; align-items:center; gap:8px;">{icon('info', 15)}Timely action reduces downtime and ensures long-term belt reliability.</div>
        <div>B.R.A.V.E. &nbsp;|&nbsp; Safer Operations &nbsp; Stronger Tomorrow</div>
    </div>
    """)
