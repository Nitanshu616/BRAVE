import time

import streamlit as st

from ui.icons import icon
from ui.components import logo_svg, render


def _body(pct: int) -> str:
    features = [
        ("shield", "RELIABLE"),
        ("bar-chart", "DATA DRIVEN"),
        ("cpu", "SMARTER MINING"),
        ("heart", "SUSTAINABLE FUTURE"),
    ]
    feat_html = "".join(
        f'<div class="feat">{icon(name, 26, color="#E0C9A0")}<span>{label}</span></div>' for name, label in features
    )
    return f"""
    <div class="brv-splash">
        <div class="brv-splash-topleft"><div class="tick"></div>MONITOR<br/>PREDICT<br/>PREVENT</div>
        <div class="brv-splash-topright">FOR A<br/>SAFER<br/>TOMORROW</div>
        <div class="brv-splash-main">
            {logo_svg(64)}
            <div class="brv-splash-title">B.R.A.V.E.</div>
            <div class="brv-splash-subtitle">BELT RUPTURE ANALYSIS &amp;<br/>VULNERABILITY ESTIMATION</div>
            <div class="brv-splash-divider"></div>
            <div class="brv-splash-tagline">INTELLIGENT MONITORING<br/>STRONGER OPERATIONS</div>
            <div class="brv-splash-progress">
                <div class="track"><div class="fill" style="width:{pct}%;"></div></div>
                <div class="pct">{pct}%</div>
            </div>
            <div class="brv-splash-loading">Loading system...</div>
            <div class="brv-splash-features">{feat_html}</div>
        </div>
        <div class="brv-splash-footer-l">SIH 2026 &nbsp;|&nbsp; TEAM CYPHER LUMINARIES</div>
        <div class="brv-splash-footer-r">v1.0.0</div>
    </div>
    """


def show():
    placeholder = st.empty()
    render(_body(100), container=placeholder)
    time.sleep(0.15)
    st.session_state.splash_shown = True
    st.rerun()
