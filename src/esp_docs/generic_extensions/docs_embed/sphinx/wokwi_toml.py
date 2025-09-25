from __future__ import annotations

import os
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

from docutils import nodes
from docutils.parsers.rst import Directive, directives

try:  # Python 3.11+
    import tomllib as _toml
except Exception:  # pragma: no cover
    import tomli as _toml  # type: ignore

from .nodes import WokwiNode


def _is_http_url(s: str) -> bool:
    try:
        p = urlparse(s)
        return p.scheme in ("http", "https")
    except Exception:
        return False


def _read_toml(path_or_url: str, srcdir: str) -> Dict:
    """
    Load TOML from http(s) or from a file path relative to the current document.
    """
    if _is_http_url(path_or_url):
        # We do not fetch over network during build; this directive expects
        # HTTP(S) sources to be resolvable outside Sphinx. We parse only if
        # Sphinx can read local cache or the file is present locally.
        # For now, only local files are supported for parsing when not embedded.
        # Users will normally point to a TOML in a repo that is also present
        # in the docs tree (recommended).
        raise ValueError(
            "wokwi-toml: parsing remote TOML over HTTP is not supported at build time. "
            "Place the TOML file in your docs tree and reference it relatively."
        )

    abs_path = os.path.normpath(os.path.join(srcdir, path_or_url))
    if not os.path.isfile(abs_path):
        raise FileNotFoundError(f"wokwi-toml: file not found: {abs_path}")
    with open(abs_path, "rb") as f:
        return _toml.load(f)


def _norm_chipset_key(label: str) -> str:
    """
    'ESP32' -> 'esp32', 'ESP32-C3' -> 'esp32-c3'
    """
    return label.strip().lower().replace(" ", "-").replace("_", "-")


def _make_url(prefix: Optional[str], path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    if _is_http_url(path):
        return path
    if not prefix:
        return None
    # Ensure trailing slash on prefix; urljoin will otherwise drop last segment.
    if not prefix.endswith("/"):
        prefix = prefix + "/"
    return urljoin(prefix, path.lstrip("/"))


class WokwiTomlDirective(Directive):
    """
    Usage inside a wokwi-tabs block:

    .. wokwi-toml:: path/to/launchpad.toml
       :project: Blink

    The TOML contains multiple projects; we choose one via :project:.
    For each chipset in the project's "chipsets" array, this directive
    generates a WokwiNode (one tab per chipset) with firmware image URL
    built from the global 'wokwi_download_server' prefix and the
    image.<chipset> path from the TOML. Diagram URLs are taken from the
    TOML (diagram.<chipset>) if present, otherwise left empty (the
    wokwi-tabs fallback with `wokwi_json_prefix` still applies).
    """
    required_arguments = 1  # toml path or http(s) url (http parsing not supported)
    optional_arguments = 0
    final_argument_whitespace = False

    option_spec = {
        "project": directives.unchanged_required,
        # Optional explicit label prefix for tabs (rarely needed)
        "label-prefix": directives.unchanged,
    }

    has_content = False

    def run(self):
        env = self.state.document.settings.env
        app = env.app
        cfg = app.config

        toml_arg = self.arguments[0].strip()
        project = self.options.get("project")
        if not project:
            raise self.error("wokwi-toml: :project: is required.")

        # Required global config (download server used to build firmware URLs)
        download_server = getattr(cfg, "wokwi_download_server", None)
        if not download_server:
            raise self.error(
                "wokwi-toml: 'wokwi_download_server' must be set in conf.py "
                "(e.g. 'https://esp.kubaandrysek.cz/arduino/')."
            )

        # Load/parse TOML (local only during build)
        try:
            data = _read_toml(toml_arg, env.srcdir)
        except Exception as e:
            raise self.error(str(e))

        # Optional TOML-level base for diagrams/images (used only when paths are relative)
        toml_fw_base = data.get("firmware_images_url")
        # Locate the project table
        if project not in data:
            raise self.error(f"wokwi-toml: project '{project}' not found in {toml_arg}")
        proj = data[project]
        chipsets: List[str] = proj.get("chipsets") or []
        if not chipsets:
            raise self.error(f"wokwi-toml: project '{project}' has no 'chipsets' array.")

        # If the given TOML arg is http(s), we can use it for the Launchpad link.
        # Otherwise (local file), skip creating a Launchpad URL (we can't guarantee hosting).
        toml_url_for_launchpad = toml_arg if _is_http_url(toml_arg) else None

        label_prefix = (self.options.get("label-prefix") or "").strip()

        out_nodes: List[nodes.Node] = []
        # for label in chipsets:
        for label in ["ESP32", "ESP32-S3"]:  # TODO remove, testing only
            key = _norm_chipset_key(label)
            img_path = "https://esp.kubaandrysek.cz/arduino/libraries/ESP32/examples/GPIO/Blink/Blink-ESP32.bin"
            if not img_path:
                # Try legacy spelling replacing '-' with nothing (unlikely but safe)
                # img_path = proj.get(f"image.{key.replace('-', '')}")
                img_path = proj.get(f"image.{key}")
            if not img_path:
                raise self.error(
                    f"wokwi-toml: missing 'image.{key}' for project '{project}'."
                )

            # diag_path = proj.get(f"diagram.{key}") or None
            diag_path = "https://esp.kubaandrysek.cz/arduino/libraries/ESP32/examples/GPIO/Blink/Blink-ESP32-diagram.json"

            firmware_url = _make_url(download_server, img_path) or _make_url(toml_fw_base, img_path)
            if not firmware_url:
                raise self.error(
                    f"wokwi-toml: could not build firmware URL for chipset '{label}'. "
                    "Provide absolute http(s) in TOML or set 'wokwi_download_server' in conf.py."
                )
            diagram_url = _make_url(toml_fw_base, diag_path)  # if None, tabs fallback may supply later

            wn = WokwiNode()
            wn["viewer_base"] = cfg.wokwi_viewer_url
            wn["diagram"] = diagram_url
            wn["firmware"] = firmware_url
            wn["width"] = getattr(cfg, "wokwi_default_width", "100%")
            wn["height"] = getattr(cfg, "wokwi_default_height", "500px")
            wn["title"] = f"Wokwi simulation — {project} ({label})"
            wn["allowfullscreen"] = getattr(cfg, "wokwi_default_allowfullscreen", True)
            wn["loading"] = getattr(cfg, "wokwi_default_loading", "lazy")
            wn["classes"] = ["wokwi-embed", "from-toml"]

            wn["tab_label"] = f"{label_prefix}{label}" if label_prefix else label
            wn["suppress_header"] = True  # rendered inside wokwi-tabs
            wn["from_toml"] = True
            if toml_url_for_launchpad:
                wn["toml_url"] = toml_url_for_launchpad

            out_nodes.append(wn)

        return out_nodes
