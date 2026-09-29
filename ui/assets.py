import base64
import functools
from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"


@functools.lru_cache(maxsize=None)
def data_uri(filename: str):
    path = ASSETS_DIR / filename
    if not path.exists():
        return None
    data = base64.b64encode(path.read_bytes()).decode()
    ext = path.suffix.lstrip(".")
    mime = "jpeg" if ext == "jpg" else ext
    return f"data:image/{mime};base64,{data}"
