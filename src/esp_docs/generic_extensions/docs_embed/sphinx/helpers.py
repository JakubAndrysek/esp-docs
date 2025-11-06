"""Helper functions for Wokwi diagram rendering and URL construction.

This module provides utility functions for validating and processing configuration
values, escaping HTML content, and constructing iframe URLs for diagram embedding.
"""

from __future__ import annotations

import html
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
    """Validate and normalize a CSS size value.
    
    Accepts strings like '500px', '100%', '50em', etc. Strips whitespace
    and validates that the value is not empty.
    
    Args:
        value: CSS size string to validate
        
    Returns:
        Normalized CSS size string
        
    Raises:
        ValueError: If value is not a string, is empty, or invalid
        
    Examples:
        css_size("500px")  # Returns "500px"
        css_size(" 100% ")  # Returns "100%"
    """
    if not isinstance(value, str):
        raise ValueError("Expected a string CSS size, e.g. '500px' or '100%'.")
    v = value.strip()
    if not v:
        raise ValueError("Width/height cannot be empty.")
    return v


def loading_choice(arg: str) -> str:
    """Validate and normalize iframe loading attribute.
    
    The loading attribute controls how the browser loads the iframe:
    - 'lazy': Deferred loading until iframe is near viewport
    - 'eager': Load immediately (default browser behavior)
    - 'auto': Browser decides the loading strategy
    
    Args:
        arg: Loading strategy string to validate
        
    Returns:
        Normalized loading attribute value
        
    Raises:
        ValueError: If value is not one of the allowed choices
        
    Examples:
        loading_choice("lazy")  # Returns "lazy"
        loading_choice("EAGER")  # Returns "eager"
    """
    v = arg.strip().lower()
    if v not in ("lazy", "eager", "auto"):
        raise ValueError("loading must be one of: lazy | eager | auto")
    return v


def iframe_url(
    base: str,
    diagram_url: str,
    firmware_url: str,
    iframe_page_params: Optional[Dict[str, str]] = None,
) -> str:
    """Construct a complete iframe URL with diagram and firmware parameters.
    
    Builds the full URL for embedding a diagram viewer iframe by combining
    the base URL with diagram and firmware URLs, plus any additional parameters.
    
    Args:
        base: Base URL of the iframe viewer (e.g., 'https://wokwi.com/experimental/viewer')
        diagram_url: URL to the Wokwi diagram JSON file
        firmware_url: URL to the compiled firmware binary
        iframe_page_params: Optional additional URL parameters to include
        
    Returns:
        Complete iframe URL with all parameters URL-encoded
        
    Examples:
        iframe_url(
            "https://wokwi.com/experimental/viewer",
            "https://example.com/diagram.json",
            "https://example.com/firmware.bin"
        )
        # Returns: "https://wokwi.com/experimental/viewer?diagram=...&firmware=..."
    """
    params: Dict[str, str] = {
        "diagram": diagram_url,
        "firmware": firmware_url,
    }
    if iframe_page_params:
        params.update(iframe_page_params)
    qs = urlencode(params, quote_via=quote, safe="")
    return base + (("?" + qs) if qs else "")
