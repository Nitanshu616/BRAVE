import re
from datetime import datetime

import streamlit as st

import config
from ui import theme as t
from ui.icons import icon


def render(html: str, container=None):
    """Render a (possibly multi-line, indented) HTML string safely.

    Streamlit's markdown parser follows CommonMark: an indented or
    blank line inside an HTML block ends the block early and the
    remainder gets parsed as a markdown indented-code-block instead of
    HTML. Collapsing everything onto one line sidesteps that entirely.
    """
    target = container or st
    target.markdown(re.sub(r"\n\s*", "", html.strip()), unsafe_allow_html=True)

NAV_ITEMS = [
    ("control_room", "Control Room", "home"),
    ("live_sensors", "Live Sensors", "activity"),
    ("belt_digital_twin", "Belt Digital Twin", "box"),
    ("anomaly_detection", "Anomaly Detection", "alert-triangle"),
    ("fault_localization", "Fault Localization", "map-pin"),
    ("predictive_maintenance", "Predictive Maintenance", "wrench"),
    ("alerts_actions", "Alerts & Actions", "bell"),
]


def sidebar(active_slug: str):
    nav_html = "".join(
        f'<a class="{"active" if slug == active_slug else ""}" href="?page={slug}" target="_self">'
        f'{icon(ic, 17)}<span>{label}</span></a>'
        for slug, label, ic in NAV_ITEMS
    )
    render(f"""
        <div class="brv-brand">
            <div class="brv-brand-row">
                {logo_svg()}
                <div class="brv-brand-title">B.R.A.V.E.</div>
            </div>
            <div class="brv-brand-sub">Belt Rupture Analysis &amp;<br/>Vulnerability Estimation</div>
        </div>
        <div class="brv-nav">{nav_html}</div>
        <div class="brv-sidebar-bottom">
            <div class="brv-sidebar-unit">
                <div class="name">{config.PLANT_NAME}</div>
                <div class="loc">{config.PLANT_LOCATION}</div>
                <div class="stat"><span class="dot"></span> Online</div>
            </div>
            <div class="brv-sidebar-footer">
                Safer Operations<br/>Stronger Tomorrow
            </div>
        </div>
    """, container=st.sidebar)


def logo_svg(size=32):
    return f"""<svg width="{size}" height="{size}" viewBox="0 0 48 40" xmlns="http://www.w3.org/2000/svg">
        <polygon points="18,4 30,36 6,36" fill="{t.RUST}"/>
        <polygon points="30,4 42,36 18,36" fill="{t.TAN}"/>
        <polygon points="24,14 34,36 14,36" fill="{t.SAGE}"/>
    </svg>"""


def header_unit_select(unit=None):
    unit = unit or config.PLANT_NAME
    return (f'<div class="brv-header-search" style="max-width:150px; justify-content:space-between; '
            f'cursor:default;"><span style="font-weight:600;">{unit}</span>{icon("chevron-down", 14)}</div>')


def page_header(title: str, subtitle: str, right_html: str = ""):
    render(f"""
    <div style="display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:22px; gap:20px;">
        <div>
            <div class="brv-page-title">{title}</div>
            <div class="brv-page-sub">{subtitle}</div>
        </div>
        <div>{right_html}</div>
    </div>
    """)


def flag_synced(text="Data synchronized"):
    return f'<div class="brv-page-flag"><span class="dot"></span>{text}</div>'


def pill(text, status_key, dot=True):
    fg, bg = t.status_colors(status_key)
    dot_html = f'<span style="width:7px;height:7px;border-radius:50%;background:{fg};"></span>' if dot else ""
    return f'<div class="brv-pill" style="background:{bg}; color:{fg};">{dot_html}{text}</div>'


def date_range_pill(text):
    return f'<div class="brv-header-search" style="max-width:340px;">{icon("calendar", 15)}<span>{text}</span>{icon("chevron-down", 13)}</div>'


def metric_card(icon_name, accent, label, value, unit="", change=None, change_dir="up",
                 good=True, progress=None, progress_color=None, caption=None, caption_color=None):
    change_html = ""
    if change is not None:
        arrow = "trending-up" if change_dir == "up" else "trending-down"
        cls = f"{change_dir} {'good' if good else 'bad'}"
        change_html = f'<span class="brv-metric-change {cls}">{icon(arrow, 12)}{change}</span>'
    progress_html = ""
    if progress is not None:
        color = progress_color or accent
        pct = max(0, min(100, progress))
        progress_html = f'<div class="brv-progress-track"><div class="brv-progress-fill" style="width:{pct}%; background:{color};"></div></div>'
    caption_html = ""
    if caption is not None:
        color = caption_color or "var(--muted)"
        caption_html = f'<div style="font-size:12.5px; color:{color}; font-weight:600; margin-top:8px;">{caption}</div>'
    unit_html = f'<span class="brv-metric-unit">{unit}</span>' if unit else ""
    value_style = ' style="font-size:17px; line-height:1.3;"' if len(str(value)) > 10 else ""
    render(f"""
    <div class="brv-card">
        <div class="brv-card-top">
            <div class="brv-icon-circle" style="background:{accent}24; color:{accent};">{icon(icon_name, 20, color=accent)}</div>
            <div style="flex:1; min-width:0;">
                <div class="brv-metric-label">{label}</div>
                <div class="brv-metric-row">
                    <span class="brv-metric-value"{value_style}>{value}</span>{unit_html}{change_html}
                </div>
                {caption_html}
            </div>
        </div>
        {progress_html}
    </div>
    """)


def sparkline_svg(values, color, width=120, height=30):
    if not values:
        return ""
    lo, hi = min(values), max(values)
    span = (hi - lo) or 1
    n = len(values)
    pts = []
    for i, v in enumerate(values):
        x = (i / (n - 1) * width) if n > 1 else 0
        y = height - ((v - lo) / span) * height
        pts.append(f"{x:.1f},{y:.1f}")
    path = " ".join(pts)
    area = f"0,{height} {path} {width},{height}"
    return (f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
            f'xmlns="http://www.w3.org/2000/svg"><polyline points="{area}" fill="{color}22" stroke="none"/>'
            f'<polyline points="{path}" fill="none" stroke="{color}" stroke-width="2" '
            f'stroke-linejoin="round" stroke-linecap="round"/></svg>')


def camera_feed(frame_b64, damage_score, top_class, connected, timestamp_text="--"):
    """Renders the vision gateway's latest annotated frame inline in the
    dashboard — no separate cv2 window. Feed it live_data.get_vision_state().
    """
    status_key = "Normal" if top_class == "NONE" else ("Critical" if damage_score >= 0.7 else "Warning")
    fg, bg = t.status_colors(status_key)

    if frame_b64:
        img_html = (f'<img src="data:image/jpeg;base64,{frame_b64}" '
                    f'style="width:100%; border-radius:10px; display:block; aspect-ratio:16/9; object-fit:cover;"/>')
    else:
        img_html = ('<div style="width:100%; aspect-ratio:16/9; background:var(--cream); '
                     'border:1px dashed var(--border); border-radius:10px; display:flex; '
                     'align-items:center; justify-content:center; color:var(--muted); font-size:13px;">'
                     'No camera signal</div>')

    conn_color = "#3C9A5F" if connected else "#C63A2E"
    render(f"""
    <div class="brv-card">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
            <div style="display:flex; align-items:center; gap:8px; color:var(--ink); font-weight:600; font-size:13.5px;">
                {icon("activity", 17)}<span>Live Camera Feed</span>
            </div>
            <div style="display:flex; align-items:center; gap:6px; font-size:12px; color:var(--muted);">
                <span style="width:7px;height:7px;border-radius:50%;background:{conn_color};"></span>
                {"Connected" if connected else "No signal"}
            </div>
        </div>
        {img_html}
        <div style="display:flex; justify-content:space-between; align-items:center; margin-top:12px;">
            <div class="brv-pill" style="background:{bg}; color:{fg};">
                <span style="width:7px;height:7px;border-radius:50%;background:{fg};"></span>
                {top_class if top_class != "NONE" else "No damage detected"}
            </div>
            <div style="font-size:12px; color:var(--muted);">Score: {damage_score:.2f} &middot; {timestamp_text}</div>
        </div>
    </div>
    """)


def sensor_card(icon_name, accent, label, value, unit, change, change_dir, good, spark_values, subtext):
    change_html = ""
    if change is not None:
        arrow = "trending-up" if change_dir == "up" else "trending-down"
        cls = f"{change_dir} {'good' if good else 'bad'}"
        change_html = f'<span class="brv-metric-change {cls}">{icon(arrow, 12)}{change}</span>'
    spark = sparkline_svg(spark_values, accent)
    render(f"""
    <div class="brv-card">
        <div style="display:flex; align-items:center; gap:8px; color:{accent}; margin-bottom:12px;">
            {icon(icon_name, 17, color=accent)}
            <span style="color:var(--ink); font-weight:600; font-size:13.5px;">{label}</span>
        </div>
        <div class="brv-metric-row" style="margin-bottom:6px;">
            <span class="brv-metric-value" style="font-size:25px;">{value}</span>
            <span class="brv-metric-unit">{unit}</span>{change_html}
        </div>
        <div style="margin:2px 0 10px -2px;">{spark}</div>
        <div style="font-size:12px; color:var(--muted);">{subtext}</div>
    </div>
    """)


def section(title, inner_html, icon_name=None, right_html="", subtitle=None):
    icon_html = f'<span style="color:var(--rust-dark);">{icon(icon_name, 18)}</span>' if icon_name else ""
    sub_html = f'<div style="color:var(--muted); font-size:12.5px; margin:-8px 0 12px 0;">{subtitle}</div>' if subtitle else ""
    render(f"""
    <div class="brv-section">
        <div class="brv-section-head" style="margin-bottom:{6 if subtitle else 14}px;">
            <div class="brv-section-title">{icon_html}{title}</div>
            <div>{right_html}</div>
        </div>
        {sub_html}
        {inner_html}
    </div>
    """)


def section_start(title, icon_name=None, right_html="", subtitle=None):
    icon_html = f'<span style="color:var(--rust-dark);">{icon(icon_name, 18)}</span>' if icon_name else ""
    sub_html = f'<div style="color:var(--muted); font-size:12.5px; margin:-6px 0 8px 0;">{subtitle}</div>' if subtitle else ""
    render(f"""
    <div class="brv-section-head" style="margin-top:2px; margin-bottom:{4 if subtitle else 10}px;">
        <div class="brv-section-title">{icon_html}{title}</div>
        <div>{right_html}</div>
    </div>
    {sub_html}
    """)


def _cell(value, mode, col_status):
    if not col_status:
        return f"<td>{value}</td>"
    fg, bg = t.status_colors(value)
    if mode == "badge":
        return f'<td><span class="brv-pill" style="background:{bg}; color:{fg};">{value}</span></td>'
    if mode == "color":
        return f'<td style="color:{fg}; font-weight:700;">{value}</td>'
    dot = f'<span style="width:7px;height:7px;border-radius:50%;background:{fg};display:inline-block;"></span>'
    return f'<td><span style="display:inline-flex;align-items:center;gap:7px;color:{fg};font-weight:600;">{dot}{value}</span></td>'


def table_html(headers, rows, dot_cols=(), badge_cols=(), color_cols=(), bold_cols=(), highlight_rows=()):
    thead = "".join(f"<th>{h}</th>" for h in headers)
    body_rows = []
    for ridx, row in enumerate(rows):
        cells = []
        for cidx, value in enumerate(row):
            if cidx in dot_cols:
                cells.append(_cell(value, "dot", True))
            elif cidx in badge_cols:
                cells.append(_cell(value, "badge", True))
            elif cidx in color_cols:
                cells.append(_cell(value, "color", True))
            elif cidx in bold_cols:
                cells.append(f"<td style='font-weight:700;'>{value}</td>")
            else:
                cells.append(f"<td>{value}</td>")
        cls = "highlight" if ridx in highlight_rows else ""
        body_rows.append(f"<tr class='{cls}'>{''.join(cells)}</tr>")
    return f"<table class='brv-table'><thead><tr>{thead}</tr></thead><tbody>{''.join(body_rows)}</tbody></table>"


def kv_list(rows):
    """rows: list of (icon_name, label, value, value_color)"""
    items = []
    for icon_name, label, value, color in rows:
        color_style = f"color:{color};" if color else ""
        items.append(f"""
        <div class="brv-kv">
            <div class="k">{icon(icon_name, 15)} {label}</div>
            <div class="v" style="{color_style}">{value}</div>
        </div>""")
    return "".join(items)


def alert_list(items):
    """items: list of dicts {severity, title, meta, time}"""
    rows = []
    for it in items:
        fg, _ = t.status_colors(it["severity"])
        rows.append(f"""
        <div class="brv-alert-row">
            <span class="brv-alert-dot" style="background:{fg};"></span>
            <div style="flex:1;">
                <div class="brv-alert-title">{it['title']}</div>
                <div class="brv-alert-meta">{it['meta']}</div>
            </div>
            <div class="brv-alert-time">{it['time']}</div>
        </div>""")
    return "".join(rows)


def schedule_list(items):
    """items: list of dicts {icon, title, priority, date}"""
    rows = []
    for it in items:
        fg, bg = t.status_colors(it["priority"])
        rows.append(f"""
        <div class="brv-alert-row">
            <div class="brv-icon-circle" style="width:32px;height:32px;background:{bg};color:{fg};">{icon(it['icon'], 15)}</div>
            <div style="flex:1;">
                <div class="brv-alert-title">{it['title']}</div>
                <div class="brv-alert-meta" style="color:{fg}; font-weight:600;">{it['priority']}</div>
            </div>
            <div class="brv-alert-time">{it['date']}</div>
        </div>""")
    return "".join(rows)


def status_legend(labels=("Normal", "Warning", "Critical")):
    parts = []
    for label in labels:
        fg, _ = t.status_colors(label)
        parts.append(f'<span style="color:{fg}; font-weight:600;">● {label}</span>')
    return '<div style="display:flex; gap:14px; font-size:12px;">' + "".join(parts) + '</div>'


def joint_map_html(joints, active_id):
    dots = []
    for j in joints:
        fg, _ = t.status_colors(j["status"])
        pulse = "pulse" if j["id"] == active_id else ""
        label_cls = "active" if j["id"] == active_id else ""
        dots.append(f"""
        <div class="brv-joint">
            <div class="brv-joint-label {label_cls}">{j['id']}</div>
            <div class="brv-joint-dot {pulse}" style="background:{fg}; color:{fg};"></div>
            <div class="brv-joint-pos">{j['position_m']} m</div>
        </div>""")
    return f"""
    <div class="brv-jointmap">
        <div class="brv-jointmap-line"></div>
        <div class="brv-jointmap-row">{''.join(dots)}</div>
        <div class="brv-jointmap-ends"><span>Head</span><span>Tail</span></div>
    </div>"""


def progress_row(label, value_text, pct, color):
    return f"""
    <div style="margin-bottom:16px;">
        <div class="brv-barlabel"><span>{label}</span><span class="val" style="color:{color};">{value_text}</span></div>
        <div class="brv-progress-track"><div class="brv-progress-fill" style="width:{max(0,min(100,pct))}%; background:{color};"></div></div>
    </div>"""


def chip_row(chips):
    return '<div class="brv-chip-row">' + "".join(f'<span class="brv-chip">{c}</span>' for c in chips) + "</div>"


def chart_legend(items):
    """items: list of (label, color, style) where style is 'solid'/'dashed'/'area'."""
    parts = []
    for label, color, style in items:
        if style == "area":
            swatch = f'<span style="width:14px;height:8px;background:{color}33;border:1px solid {color};display:inline-block;border-radius:2px;"></span>'
        else:
            border = "dashed" if style == "dashed" else "solid"
            swatch = f'<span style="width:16px;height:0;border-top:2px {border} {color};display:inline-block;"></span>'
        parts.append(f'<span style="display:inline-flex;align-items:center;gap:5px;">{swatch}{label}</span>')
    return '<div style="display:flex; gap:14px; font-size:12px; color:var(--muted); flex-wrap:wrap;">' + "".join(parts) + '</div>'


def icon_list(items):
    rows = []
    for icon_name, text in items:
        rows.append(f'<div style="display:flex; align-items:center; gap:10px; padding:8px 0; font-size:13.5px; color:var(--ink);">{icon(icon_name, 16)}{text}</div>')
    return "".join(rows)


def mini_grid(cards, cols=2):
    items = []
    for card in cards:
        color = card.get("color", "var(--ink)")
        items.append(f"""
        <div style="background:var(--cream); border:1px solid var(--border); border-radius:12px; padding:14px;">
            <div style="display:flex; align-items:center; gap:8px; color:var(--muted); font-size:12.5px; font-weight:600; margin-bottom:6px;">{icon(card['icon'], 15)}{card['title']}</div>
            <div style="font-weight:700; color:{color}; font-size:14.5px;">{card['status']}</div>
            <div style="font-size:12px; color:var(--muted); margin-top:2px;">{card['subtitle']}</div>
        </div>""")
    return f'<div style="display:grid; grid-template-columns:repeat({cols},1fr); gap:12px;">' + "".join(items) + '</div>'


def recommendation(text, icon_name="lightbulb"):
    return f'<div class="brv-recommend">{icon(icon_name, 20)}<div>{text}</div></div>'