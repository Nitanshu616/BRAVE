from datetime import datetime


def time_ago(dt):
    if dt is None:
        return "--"
    secs = int((datetime.now() - dt).total_seconds())
    if secs < 5:
        return "just now"
    if secs < 60:
        return f"{secs} sec ago"
    mins = secs // 60
    if mins < 60:
        return f"{mins} min ago"
    hours = mins // 60
    if hours < 24:
        return f"{hours}h {mins % 60}m ago"
    return f"{hours // 24}d ago"


def fmt(value, decimals=1, suffix=""):
    if value is None:
        return "--"
    try:
        return f"{float(value):.{decimals}f}{suffix}"
    except (TypeError, ValueError):
        return "--"
