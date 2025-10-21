from __future__ import annotations

from pathlib import Path

from .sphinx.nodes import WokwiNode, WokwiTabsNode, TabListNode, TabPanelNode
from .sphinx.directives import WokwiDirective, WokwiExampleDirective
from .sphinx import html
from sphinx.application import Sphinx


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
    app.add_config_value("about_wokwi_url", None, "env")
    app.add_config_value("wokwi_esp_launchpad_url", "https://espressif.github.io/esp-launchpad", "env")
    app.add_config_value("docs_embed_root", None, "env")  # e.g. "../.."
    app.add_config_value("docs_embed_store_prefix", None, "env")

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
    app.add_directive("wokwi-example", WokwiExampleDirective)

    app.connect("builder-inited", _register_static)

    return {
        "version": "0.7.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
