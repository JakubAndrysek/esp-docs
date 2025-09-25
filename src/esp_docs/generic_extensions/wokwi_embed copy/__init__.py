from __future__ import annotations

from pathlib import Path

from . import nodes as _nodes
from . import directives as _directives
from . import html as _html
from sphinx.application import Sphinx

# --- Export node classes at package level for pickle compatibility ---
# Old pickled doctrees may reference esp_docs.generic_extensions.wokwi_embed.WokwiTabsNode
# Make those names available here to allow unpickling.
WokwiNode = _nodes.WokwiNode
WokwiTabsNode = _nodes.WokwiTabsNode
TabListNode = _nodes.TabListNode
TabPanelNode = _nodes.TabPanelNode

__all__ = [
    "WokwiNode",
    "WokwiTabsNode",
    "TabListNode",
    "TabPanelNode",
    "setup",
]


def _register_static(app: Sphinx) -> None:
    """
    Ensure our packaged _static dir is available to the HTML builder.
    """
    pkg_static = Path(__file__).parent / "_static"
    # Make sure html_static_path is a list and contains our package static dir.
    if getattr(app.config, "html_static_path", None) is None:
        app.config.html_static_path = []
    if str(pkg_static) not in app.config.html_static_path:
        app.config.html_static_path.append(str(pkg_static))

    # Add our assets (relative filenames, Sphinx copies from html_static_path)
    app.add_css_file("wokwi_embed.css")
    app.add_js_file("wokwi_embed.js")


def setup(app: Sphinx) -> None:
    # Config defaults (project can override in conf.py)
    app.add_config_value(
        "wokwi_viewer_url", "https://wokwi.com/experimental/viewer", "env"
    )
    app.add_config_value("wokwi_default_width", "100%", "env")
    app.add_config_value("wokwi_default_height", "500px", "env")
    app.add_config_value("wokwi_default_allowfullscreen", True, "env")
    app.add_config_value("wokwi_default_loading", "lazy", "env")
    app.add_config_value(
        "wokwi_json_prefix", None, "env"
    )  # e.g. "https://example.com/wokwi"
    app.add_config_value("wokwi_info_url", None, "env")  # show info icon only if set

    # Nodes
    app.add_node(
        _nodes.WokwiNode,
        html=(_html.visit_wokwi_html, _html.depart_wokwi_html),
        singlehtml=(_html.visit_wokwi_html, _html.depart_wokwi_html),
        dirhtml=(_html.visit_wokwi_html, _html.depart_wokwi_html),
        epub=(_html.visit_wokwi_html, _html.depart_wokwi_html),
        text=(_html.visit_wokwi_text, _html.depart_wokwi_text),
        latex=(_html.visit_wokwi_latex, _html.depart_wokwi_latex),
        man=(_html.visit_wokwi_text, _html.depart_wokwi_text),
    )
    app.add_node(
        _nodes.WokwiTabsNode,
        html=(_html.visit_wokwi_tabs_html, _html.depart_wokwi_tabs_html),
        singlehtml=(_html.visit_wokwi_tabs_html, _html.depart_wokwi_tabs_html),
        dirhtml=(_html.visit_wokwi_tabs_html, _html.depart_wokwi_tabs_html),
        epub=(_html.visit_wokwi_tabs_html, _html.depart_wokwi_tabs_html),
        text=(_html.visit_wokwi_tabs_text, _html.depart_wokwi_tabs_text),
        latex=(_html.visit_wokwi_tabs_latex, _html.depart_wokwi_tabs_latex),
        man=(_html.visit_wokwi_tabs_text, _html.depart_wokwi_tabs_text),
    )
    app.add_node(
        _nodes.TabListNode,
        html=(_html.visit_tablist_html, _html.depart_tablist_html),
        singlehtml=(_html.visit_tablist_html, _html.depart_tablist_html),
        dirhtml=(_html.visit_tablist_html, _html.depart_tablist_html),
        epub=(_html.visit_tablist_html, _html.depart_tablist_html),
        text=(_html.visit_tablist_text, _html.depart_tablist_text),
        latex=(_html.visit_tablist_latex, _html.depart_tablist_latex),
        man=(_html.visit_tablist_text, _html.depart_tablist_text),
    )
    app.add_node(
        _nodes.TabPanelNode,
        html=(_html.visit_tabpanel_html, _html.depart_tabpanel_html),
        singlehtml=(_html.visit_tabpanel_html, _html.depart_tabpanel_html),
        dirhtml=(_html.visit_tabpanel_html, _html.depart_tabpanel_html),
        epub=(_html.visit_tabpanel_html, _html.depart_tabpanel_html),
        text=(_html.visit_tabpanel_text, _html.depart_tabpanel_text),
        latex=(_html.visit_tabpanel_latex, _html.depart_tabpanel_latex),
        man=(_html.visit_tabpanel_text, _html.depart_tabpanel_text),
    )

    # Directives
    app.add_directive("wokwi", _directives.WokwiDirective)
    app.add_directive("wokwi-tabs", _directives.WokwiTabsDirective)

    # Provide our CSS & JS
    app.connect("builder-inited", _register_static)

    return {
        "version": "0.0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
