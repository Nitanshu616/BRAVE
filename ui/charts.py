import plotly.graph_objects as go

import config
from ui import theme as t

FONT = dict(family="DM Sans, sans-serif", color=t.INK, size=12)


def _base_layout(height=320, legend=True):
    layout = dict(
        height=height,
        margin=dict(l=6, r=6, t=10, b=6),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=FONT,
        hoverlabel=dict(bgcolor="white", bordercolor=t.BORDER, font=FONT),
        xaxis=dict(showgrid=False, zeroline=False, linecolor=t.BORDER, tickfont=dict(size=11, color=t.MUTED)),
        yaxis=dict(showgrid=True, gridcolor="#EFE8D8", zeroline=False, tickfont=dict(size=11, color=t.MUTED)),
    )
    if legend:
        layout["legend"] = dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                                 font=dict(size=11, color=t.MUTED))
    else:
        layout["showlegend"] = False
    return layout


def belt_health_trend(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["time"], y=df["health"], mode="lines", line=dict(color=t.RUST_DARK, width=2.4),
        fill="tozeroy", fillcolor="rgba(190,83,53,0.12)", name="Belt Health", showlegend=False,
    ))
    fig.add_hline(y=config.WARNING_THRESHOLD, line=dict(color=t.AMBER, width=1.4, dash="dash"),
                  annotation_text="Warning Threshold", annotation_position="top left",
                  annotation_font=dict(size=11, color=t.AMBER))
    fig.add_hline(y=config.CRITICAL_THRESHOLD, line=dict(color=t.RED, width=1.4, dash="dash"),
                  annotation_text="Critical Threshold", annotation_position="bottom left",
                  annotation_font=dict(size=11, color=t.RED))
    last = df.iloc[-1]
    fig.add_annotation(x=last["time"], y=last["health"], text=f"{last['health']:.0f}%",
                        showarrow=False, yshift=22, bgcolor=t.INK, font=dict(color="white", size=12),
                        borderpad=6, bordercolor=t.INK, borderwidth=1)
    fig.add_trace(go.Scatter(x=[last["time"]], y=[last["health"]], mode="markers",
                              marker=dict(color=t.RUST_DARK, size=8), showlegend=False))
    fig.update_layout(**_base_layout(legend=False), yaxis_range=[0, 100])
    return fig


def telemetry_chart(df):
    series = [
        ("vibration_mm_s", "Vibration (mm/s)", t.RED),
        ("temperature_c", "Temperature (°C)", t.AMBER),
        ("rpm", "Roller Speed (RPM/10)", t.GREEN),
        ("position_mm", "Belt Position (mm/10)", "#6B4A2E"),
    ]
    fig = go.Figure()
    for col, name, color in series:
        y = df[col] / 10 if col in ("rpm", "position_mm") else df[col]
        fig.add_trace(go.Scatter(x=df["time"], y=y, mode="lines+markers", name=name,
                                  line=dict(color=color, width=2), marker=dict(size=3)))
    fig.update_layout(**_base_layout(height=330), hovermode="x unified")
    return fig


def anomaly_trend_chart(df, threshold=config.ANOMALY_THRESHOLD):
    colors = {"Vibration": t.RED, "Temperature": t.AMBER, "Tension": t.GREEN, "Acoustic": "#6B4A2E"}
    fig = go.Figure()
    for col, color in colors.items():
        fig.add_trace(go.Scatter(x=df["time"], y=df[col], mode="lines", name=col,
                                  line=dict(color=color, width=2)))
    fig.add_hline(y=threshold, line=dict(color=t.RED, width=1.4, dash="dash"),
                  annotation_text=f"Anomaly Threshold ({threshold:.1f})", annotation_position="top left",
                  annotation_font=dict(size=11, color=t.RED))
    peak_idx = df["Vibration"].idxmax()
    peak = df.loc[peak_idx]
    if peak["Vibration"] >= threshold:
        fig.add_trace(go.Scatter(x=[peak["time"]], y=[peak["Vibration"]], mode="markers",
                                  marker=dict(color=t.RED, size=11, line=dict(color="white", width=2)),
                                  showlegend=False))
        fig.add_annotation(x=peak["time"], y=peak["Vibration"], yshift=32,
                            text=f"Anomaly Detected<br>Score: {peak['Vibration']:.2f}",
                            showarrow=False, bgcolor="#FBEFE9", bordercolor=t.RED, borderwidth=1,
                            borderpad=6, font=dict(size=11, color=t.RED))
    fig.update_layout(**_base_layout(height=330), yaxis_range=[0, 1.05])
    return fig


def failure_probability_bars(labels, values):
    colors = [t.RED if v >= 60 else (t.AMBER if v >= 25 else t.GREEN) for v in values]
    fig = go.Figure(go.Bar(x=labels, y=values, marker_color=colors, text=[f"{v}%" for v in values],
                            textposition="outside", width=0.55))
    fig.update_layout(**_base_layout(height=280, legend=False), yaxis_range=[0, 100],
                       yaxis_title="Probability (%)")
    return fig


def health_forecast_chart(df, failure_days, failure_date):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["month"], y=df["upper"], mode="lines", line=dict(width=0),
                              showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=df["month"], y=df["lower"], mode="lines", line=dict(width=0),
                              fill="tonexty", fillcolor="rgba(198,58,46,0.14)",
                              name="Confidence Range", hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=df["month"], y=df["actual"], mode="lines+markers", name="Actual",
                              line=dict(color=t.INK, width=2.4), marker=dict(size=6)))
    fig.add_trace(go.Scatter(x=df["month"], y=df["predicted"], mode="lines+markers", name="Predicted",
                              line=dict(color=t.RED, width=2.2, dash="dash"), marker=dict(size=6)))
    fig.add_hline(y=20, line=dict(color=t.MUTED, width=1.2, dash="dot"), annotation_text="Failure Threshold",
                  annotation_position="bottom right", annotation_font=dict(size=10, color=t.MUTED))
    fail_x = df["month"].iloc[-1]
    fail_y = df["predicted"].iloc[-1]
    fig.add_vline(x=fail_x, line=dict(color=t.RED, width=1.2, dash="dash"))
    fig.add_annotation(x=fail_x, y=max(fail_y, 30) + 18, text=f"Predicted Failure<br>in {failure_days} Days<br>({failure_date})",
                        showarrow=False, bgcolor="#FBEFE9", bordercolor=t.RED, borderwidth=1, borderpad=6,
                        font=dict(size=11, color=t.RED))
    fig.update_layout(**_base_layout(height=340, legend=False), yaxis_range=[0, 100], yaxis_title="Health Index")
    return fig


def alert_trend_chart(df):
    fig = go.Figure()
    for col, color in [("Critical", t.RED), ("Warning", t.AMBER), ("Info", "#9AA3B5")]:
        fig.add_trace(go.Bar(x=df["day"], y=df[col], name=col, marker_color=color))
    fig.update_layout(**_base_layout(height=280), barmode="stack", yaxis_title="Number of Alerts")
    return fig


def anomaly_confidence_bars(labels, values):
    colors = [t.RED if v >= 70 else (t.AMBER if v >= 40 else t.GREEN) for v in values]
    fig = go.Figure(go.Bar(x=values, y=labels, orientation="h", marker_color=colors,
                            text=[f"{v}%" for v in values], textposition="outside"))
    fig.update_layout(**_base_layout(height=260, legend=False), xaxis_range=[0, 100])
    return fig
