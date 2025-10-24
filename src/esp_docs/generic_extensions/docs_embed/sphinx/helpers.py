from __future__ import annotations

import html
import re
from typing import Dict, Optional
from urllib.parse import urlencode, quote

__all__ = [
    "_escape",
    "css_size",
    "loading_choice",
    "iframe_url",
]

_escape = html.escape


def css_size(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("Expected a string CSS size, e.g. '500px' or '100%'.")
    v = value.strip()
    if not v:
        raise ValueError("Width/height cannot be empty.")
    return v


def loading_choice(arg: str) -> str:
    v = arg.strip().lower()
    if v not in ("lazy", "eager", "auto"):
        raise ValueError("loading must be one of: lazy | eager | auto")
    return v




def iframe_url(base: str, diagram_url: str, firmware_url: str, iframe_page_params: Optional[Dict[str, str]] = None) -> str:
    params: Dict[str, str] = {
        "diagram": diagram_url,
        "firmware": firmware_url,
    }
    if iframe_page_params:
        params.update(iframe_page_params)
    qs = urlencode(params, quote_via=quote, safe="")
    return base + (("?" + qs) if qs else "")
