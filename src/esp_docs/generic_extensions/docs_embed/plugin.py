from __future__ import annotations

from pathlib import Path

# from .sphinx import helpers
from .sphinx.nodes import WokwiNode, WokwiTabsNode, TabListNode, TabPanelNode
from .sphinx.directives import WokwiDirective, WokwiTabsDirective
from .sphinx import html
from .sphinx.wokwi_toml import WokwiTomlDirective
from sphinx.application import Sphinx

# __all__ = [
#     "WokwiNode",
#     "WokwiTabsNode",
#     "TabListNode",
#     "TabPanelNode",
#     "setup",
# ]


def _register_static(app: Sphinx) -> None:
    pkg_static = Path(__file__).parent / "_static"
    if getattr(app.config, "html_static_path", None) is None:
        app.config.html_static_path = []
    if str(pkg_static) not in app.config.html_static_path:
        app.config.html_static_path.append(str(pkg_static))
    app.add_css_file("wokwi_embed.css")
    app.add_js_file("wokwi_embed.js")


def setup(app: Sphinx) -> None:
    # Config defaults (project can override in conf.py)
    app.add_config_value("wokwi_viewer_url", "https://wokwi.com/experimental/viewer", "env")
    app.add_config_value("wokwi_default_width", "100%", "env")
    app.add_config_value("wokwi_default_height", "500px", "env")
    app.add_config_value("wokwi_default_allowfullscreen", True, "env")
    app.add_config_value("wokwi_default_loading", "lazy", "env")
    app.add_config_value("wokwi_json_prefix", None, "env")
    app.add_config_value("wokwi_info_url", None, "env")

    # NEW: required for wokwi-toml (prefix for firmware binaries)
    app.add_config_value("wokwi_download_server", None, "env")  # e.g. "https://esp.kubaandrysek.cz/arduino/"
    # NEW: ESP Launchpad integration (button on the right)
    app.add_config_value("wokwi_esp_launchpad_base", "https://espressif.github.io/esp-launchpad/", "env")
    app.add_config_value(
        "wokwi_launchpad_icon_url",
        "https://raw.githubusercontent.com/espressif/esp-launchpad/24bb22db7e4d6b2182e054d2f482532511c60475/assets/esp_launchpad.svg",
        "env",
    )

    # Nodes
    app.add_node(
        WokwiNode,
        html=(html.visit_wokwi_html, html.depart_wokwi_html),
        singlehtml=(html.visit_wokwi_html, html.depart_wokwi_html),
        dirhtml=(html.visit_wokwi_html, html.depart_wokwi_html),
        epub=(html.visit_wokwi_html, html.depart_wokwi_html),
        text=(html.visit_wokwi_text, html.depart_wokwi_text),
        latex=(html.visit_wokwi_latex, html.depart_wokwi_latex),
        man=(html.visit_wokwi_text, html.depart_wokwi_text),
    )
    app.add_node(
        WokwiTabsNode,
        html=(html.visit_wokwi_tabs_html, html.depart_wokwi_tabs_html),
        singlehtml=(html.visit_wokwi_tabs_html, html.depart_wokwi_tabs_html),
        dirhtml=(html.visit_wokwi_tabs_html, html.depart_wokwi_tabs_html),
        epub=(html.visit_wokwi_tabs_html, html.depart_wokwi_tabs_html),
        text=(html.visit_wokwi_tabs_text, html.depart_wokwi_tabs_text),
        latex=(html.visit_wokwi_tabs_latex, html.depart_wokwi_tabs_latex),
        man=(html.visit_wokwi_tabs_text, html.depart_wokwi_tabs_text),
    )
    app.add_node(
        TabListNode,
        html=(html.visit_tablist_html, html.depart_tablist_html),
        singlehtml=(html.visit_tablist_html, html.depart_tablist_html),
        dirhtml=(html.visit_tablist_html, html.depart_tablist_html),
        epub=(html.visit_tablist_html, html.depart_tablist_html),
        text=(html.visit_tablist_text, html.depart_tablist_text),
        latex=(html.visit_tablist_latex, html.depart_tablist_latex),
        man=(html.visit_tablist_text, html.depart_tablist_text),
    )
    app.add_node(
        TabPanelNode,
        html=(html.visit_tabpanel_html, html.depart_tabpanel_html),
        singlehtml=(html.visit_tabpanel_html, html.depart_tabpanel_html),
        dirhtml=(html.visit_tabpanel_html, html.depart_tabpanel_html),
        epub=(html.visit_tabpanel_html, html.depart_tabpanel_html),
        text=(html.visit_tabpanel_text, html.depart_tabpanel_text),
        latex=(html.visit_tabpanel_latex, html.depart_tabpanel_latex),
        man=(html.visit_tabpanel_text, html.depart_tabpanel_text),
    )

    # Directives
    app.add_directive("wokwi", WokwiDirective)
    app.add_directive("wokwi-tabs", WokwiTabsDirective)
    app.add_directive("wokwi-toml", WokwiTomlDirective)  # NEW

    app.connect("builder-inited", _register_static)

    return {
        "version": "0.6.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
