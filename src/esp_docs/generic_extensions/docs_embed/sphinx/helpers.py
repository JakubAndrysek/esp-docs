from __future__ import annotations

import html
import re
from typing import Dict, Optional
from urllib.parse import urlencode, quote

__all__ = [
    "_escape",
    "css_size",
    "loading_choice",
    "slug_lower",
    "build_viewer_url",
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


def slug_lower(name: str) -> str:
    s = re.sub(r"\s+", "-", name.strip().lower())
    s = re.sub(r"[^a-z0-9\-]", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s


def build_viewer_url(base: str, diagram: Optional[str], firmware: Optional[str]) -> str:
    params: Dict[str, str] = {}
    if diagram:
        params["diagram"] = diagram
    if firmware:
        params["firmware"] = firmware
    qs = urlencode(params, quote_via=quote, safe="")
    return base + (("?" + qs) if qs else "")


# expose directives validators for convenience where needed
css_size_directive = css_size
loading_choice_directive = loading_choice
