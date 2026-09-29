"""Minimal inline-SVG line icons (Feather-style geometry), used everywhere
instead of an icon font so the app has zero extra network dependency."""

_PATHS = {
    "home": '<path d="M3 11.5 12 4l9 7.5"/><path d="M5.5 10v9.5a1 1 0 0 0 1 1H9a1 1 0 0 0 1-1V15a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v4.5a1 1 0 0 0 1 1h2.5a1 1 0 0 0 1-1V10"/>',
    "activity": '<polyline points="2.5,13 7.5,13 9.5,6.5 14,19 16,13 21.5,13"/>',
    "box": '<path d="M12 3 3.5 7v10L12 21l8.5-4V7Z"/><path d="M3.5 7 12 11l8.5-4"/><line x1="12" y1="11" x2="12" y2="21"/>',
    "alert-triangle": '<path d="M12 3.5 22 20H2Z"/><line x1="12" y1="10" x2="12" y2="14.5"/><circle cx="12" cy="17.3" r="0.9" fill="currentColor" stroke="none"/>',
    "map-pin": '<path d="M12 21s6.5-6.2 6.5-11.5a6.5 6.5 0 0 0-13 0C5.5 14.8 12 21 12 21Z"/><circle cx="12" cy="9.3" r="2.4"/>',
    "wrench": '<path d="M14.7 6.3a4 4 0 0 1-5 5.1L4.5 16.6a1.8 1.8 0 0 0 2.5 2.5l5.2-5.2a4 4 0 0 1 5.1-5l-2.6 2.6-2-2Z"/>',
    "bell": '<path d="M6 9a6 6 0 0 1 12 0c0 4.2 1.6 5.6 2 6H4c0.4-0.4 2-1.8 2-6Z"/><path d="M9.7 18a2.3 2.3 0 0 0 4.6 0"/>',
    "heart": '<path d="M12 20s-7.3-4.4-9.8-9.2A5.3 5.3 0 0 1 12 6a5.3 5.3 0 0 1 9.8 4.8C19.3 15.6 12 20 12 20Z"/>',
    "link": '<path d="M9 13.5a3.8 3.8 0 0 0 5.6 0.4L17.7 11a3.8 3.8 0 1 0-5.3-5.3L11 7"/><path d="M15 10.5a3.8 3.8 0 0 0-5.6-0.4L6.3 13a3.8 3.8 0 1 0 5.3 5.3L13 17"/>',
    "clock": '<circle cx="12" cy="12" r="8.5"/><polyline points="12,7.5 12,12 15.5,14"/>',
    "building": '<path d="M4 21V8.5L11 4v17"/><path d="M11 21V10l9 3v8"/><line x1="7.5" y1="11" x2="7.5" y2="11.01"/><line x1="7.5" y1="15" x2="7.5" y2="15.01"/>',
    "gauge": '<circle cx="12" cy="13" r="8.5"/><path d="M7.5 16a5.5 5.5 0 0 1 9-4.3"/><line x1="12" y1="13" x2="15.5" y2="9.7"/>',
    "thermometer": '<path d="M12 3.5a2 2 0 0 0-2 2v9.9a3.8 3.8 0 1 0 4 0V5.5a2 2 0 0 0-2-2Z"/>',
    "cpu": '<rect x="6" y="6" width="12" height="12" rx="2"/><line x1="9.5" y1="2" x2="9.5" y2="6"/><line x1="14.5" y1="2" x2="14.5" y2="6"/><line x1="9.5" y1="18" x2="9.5" y2="22"/><line x1="14.5" y1="18" x2="14.5" y2="22"/>',
    "ruler": '<line x1="3" y1="12" x2="21" y2="12"/><line x1="6.5" y1="9" x2="6.5" y2="15"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="17.5" y1="9" x2="17.5" y2="15"/>',
    "search": '<circle cx="11" cy="11" r="6.5"/><line x1="20" y1="20" x2="15.8" y2="15.8"/>',
    "calendar": '<rect x="3.5" y="5" width="17" height="15.5" rx="2"/><line x1="3.5" y1="9.8" x2="20.5" y2="9.8"/><line x1="8" y1="3" x2="8" y2="6.5"/><line x1="16" y1="3" x2="16" y2="6.5"/>',
    "shield": '<path d="M12 3 19 6v5.5c0 5-3.2 7.8-7 9-3.8-1.2-7-4-7-9V6Z"/>',
    "target": '<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="3"/>',
    "lightbulb": '<path d="M9.3 18.5h5.4"/><path d="M10.2 21.5h3.6"/><path d="M12 2.5a6.3 6.3 0 0 0-3.8 11.3c0.7 0.6 1.3 1.6 1.3 2.7h5c0-1.1 0.6-2.1 1.3-2.7A6.3 6.3 0 0 0 12 2.5Z"/>',
    "clipboard": '<rect x="5.5" y="4" width="13" height="17.5" rx="2"/><path d="M9 4V3a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v1"/><line x1="8.5" y1="11" x2="15.5" y2="11"/><line x1="8.5" y1="15" x2="15.5" y2="15"/>',
    "sliders": '<line x1="4" y1="6.5" x2="20" y2="6.5"/><circle cx="9" cy="6.5" r="2"/><line x1="4" y1="12" x2="20" y2="12"/><circle cx="15" cy="12" r="2"/><line x1="4" y1="17.5" x2="20" y2="17.5"/><circle cx="7.5" cy="17.5" r="2"/>',
    "radio": '<circle cx="12" cy="12" r="1.4" fill="currentColor" stroke="none"/><path d="M8.8 8.8a4.6 4.6 0 0 1 6.4 0"/><path d="M5.8 5.8a9 9 0 0 1 12.4 0"/>',
    "chevron-down": '<polyline points="6,9.5 12,15.5 18,9.5"/>',
    "bar-chart": '<line x1="5" y1="21" x2="5" y2="12"/><line x1="12" y1="21" x2="12" y2="7"/><line x1="19" y1="21" x2="19" y2="15"/>',
    "trending-up": '<polyline points="3,17 10,10 14,14 21,6"/><polyline points="15,6 21,6 21,12"/>',
    "trending-down": '<polyline points="3,7 10,14 14,10 21,18"/><polyline points="15,18 21,18 21,12"/>',
    "check-circle": '<circle cx="12" cy="12" r="8.5"/><polyline points="8,12.3 11,15.3 16.5,9"/>',
    "info": '<circle cx="12" cy="12" r="8.5"/><line x1="12" y1="11" x2="12" y2="16.5"/><line x1="12" y1="7.5" x2="12" y2="7.5"/>',
    "user": '<circle cx="12" cy="8.5" r="3.5"/><path d="M4.5 20c1-3.6 4.2-5.5 7.5-5.5s6.5 1.9 7.5 5.5"/>',
    "database": '<ellipse cx="12" cy="6" rx="7.5" ry="3"/><path d="M4.5 6v12c0 1.7 3.4 3 7.5 3s7.5-1.3 7.5-3V6"/><path d="M4.5 12c0 1.7 3.4 3 7.5 3s7.5-1.3 7.5-3"/>',
    "wifi": '<path d="M3 8.5a13 13 0 0 1 18 0"/><path d="M6.3 12a8.5 8.5 0 0 1 11.4 0"/><path d="M9.6 15.5a4 4 0 0 1 4.8 0"/><circle cx="12" cy="19" r="1" fill="currentColor" stroke="none"/>',
}


def icon(name: str, size: int = 18, color: str = "currentColor", stroke_width: float = 1.9) -> str:
    body = _PATHS.get(name, _PATHS["info"])
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" '
        f'stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg">{body}</svg>'
    )
