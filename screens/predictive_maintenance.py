import streamlit as st

from data import live_data
from ui import components as c
from ui import charts
from ui import theme as t
from ui.icons import icon


def _health_color(pct):
    if pct >= 75:
        return t.GREEN
    if pct >= 50:
        return t.AMBER
    return t.RED


def render():
    c.page_header("Predictive Maintenance",
                  "AI-driven predictions to prevent failures and ensure continuous operation")

    pred = live_data.get_predictive()

    cols = st.columns(5)
    with cols[0]:
        c.metric_card("calendar", "#8A6A42", "Next Predicted Failure", str(pred["predicted_failure_days"]), "Days",
                      caption=f"({pred['predicted_failure_date']}) {pred['active_joint']}")
    with cols[1]:
        c.metric_card("alert-triangle", t.RED, "Failure Probability", f"{pred['failure_probability_pct']:.0f}", "%",
                      change="+12% from last week", change_dir="up", good=False)
    with cols[2]:
        c.metric_card("wrench", t.RED, "Maintenance Urgency", pred["urgency"], "",
                      caption="● Action recommended" if pred["urgency"] == "High" else "● Monitor",
                      caption_color=t.RED if pred["urgency"] == "High" else t.AMBER)
    with cols[3]:
        c.metric_card("bar-chart", t.SAGE, "Overall System Health", f"{pred['overall_health_pct']:.0f}", "%",
                      change="-6% from last week", change_dir="down", good=False)
    with cols[4]:
        c.metric_card("calendar", t.SAGE, "Scheduled Maintenance", str(pred["scheduled_count"]), "Tasks",
                      caption="In next 30 days")

    st.write("")
    with st.container(border=True):
        head_l, head_r = st.columns([2, 1.6])
        with head_l:
            st.markdown(f'<div class="brv-section-title">{icon("bar-chart", 18)}Health Index Prediction ({pred["active_joint"]})</div>',
                        unsafe_allow_html=True)
            st.markdown('<div style="color:var(--muted); font-size:12.5px; margin:-4px 0 6px 0;">'
                        'AI model prediction of component health over time</div>', unsafe_allow_html=True)
        with head_r:
            st.markdown(f'<div style="padding-top:10px;">{c.chart_legend([("Actual", t.INK, "solid"), ("Predicted", t.RED, "dashed"), ("Confidence Range", t.RED, "area")])}</div>',
                        unsafe_allow_html=True)
        st.plotly_chart(charts.health_forecast_chart(pred["forecast"], pred["predicted_failure_days"], pred["predicted_failure_date"]),
                         use_container_width=True, config={"displayModeBar": False})

    left, right = st.columns([1.1, 1])
    with left:
        with st.container(border=True):
            c.section_start("Failure Probability (Next 30 Days)", icon_name="bar-chart")
            labels = list(pred["fail_prob_by_joint"].keys())
            values = list(pred["fail_prob_by_joint"].values())
            st.plotly_chart(charts.failure_probability_bars(labels, values), use_container_width=True,
                             config={"displayModeBar": False})
    with right:
        rows = [[m["joint"], m["task"], m["priority"], m["date"], m["status"]] for m in pred["schedule"]]
        c.section("Maintenance Schedule (Next 30 Days)",
                  c.table_html(["Joint ID", "Task", "Priority", "Scheduled Date", "Status"], rows,
                              badge_cols={2, 4}, bold_cols={0}),
                  icon_name="bar-chart",
                  right_html='<a class="brv-section-link" href="?page=predictive_maintenance" target="_self">View All →</a>')

    left2, right2 = st.columns(2)
    with left2:
        rows_html = "".join(
            c.progress_row(label, f"{value:.0f}%", value, _health_color(value))
            for label, value in pred["component_health"].items()
        )
        c.section("Component Health Overview", rows_html, icon_name="sliders")
    with right2:
        banner = c.recommendation(
            f"High probability of failure at Joint {pred['active_joint']} ({pred['failure_probability_pct']:.0f}%). "
            f"Schedule maintenance immediately." if pred["urgency"] == "High" else
            f"Joint {pred['active_joint']} is trending toward reduced health. Continue monitoring.",
            icon_name="alert-triangle")
        checklist = c.icon_list([
            ("wrench", "Inspect joint, check for wear and misalignment"),
            ("sliders", "Verify belt tension, splice condition and roller alignment"),
            ("calendar", "Plan shutdown during low production window"),
        ])
        c.section("AI Recommendation", banner + checklist, icon_name="lightbulb")
