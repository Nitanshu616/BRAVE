"""Color tokens shared between CSS (styles.py) and Plotly figures (charts.py)."""

CREAM = "#F4EFE5"
CREAM_DARK = "#EDE6D8"
CARD = "#FDFBF7"
BORDER = "#E7DFCE"

INK = "#2A2118"
MUTED = "#8B8171"

SIDEBAR_TOP = "#241a12"
SIDEBAR_BOTTOM = "#3c2a19"

RUST = "#BE5335"
RUST_DARK = "#A6462B"
SAGE = "#89966B"
TAN = "#CDA46B"

GREEN = "#3E8E5B"
GREEN_BG = "#E3F0E1"
AMBER = "#D9932D"
AMBER_BG = "#FBEAD1"
RED = "#C63A2E"
RED_BG = "#F8DCD6"
INFO = "#6B7A99"
INFO_BG = "#E4E8F0"

STATUS_COLORS = {
    "normal": (GREEN, GREEN_BG),
    "healthy": (GREEN, GREEN_BG),
    "online": (GREEN, GREEN_BG),
    "low": (GREEN, GREEN_BG),
    "resolved": (GREEN, GREEN_BG),
    "scheduled": (RED, RED_BG),
    "warning": (AMBER, AMBER_BG),
    "medium": (AMBER, AMBER_BG),
    "acknowledged": (AMBER, AMBER_BG),
    "planned": (AMBER, AMBER_BG),
    "investigating": (AMBER, AMBER_BG),
    "monitoring": (AMBER, AMBER_BG),
    "critical": (RED, RED_BG),
    "high": (RED, RED_BG),
    "offline": (RED, RED_BG),
    "open": (RED, RED_BG),
    "urgent": (RED, RED_BG),
    "info": (INFO, INFO_BG),
}


def status_colors(label: str):
    return STATUS_COLORS.get(str(label).strip().lower(), (MUTED, "#EFEAE0"))
