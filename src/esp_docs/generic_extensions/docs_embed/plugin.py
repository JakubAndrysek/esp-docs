from __future__ import annotations

import os
from pathlib import Path

from .sphinx.nodes import WokwiNode, WokwiTabsNode, TabListNode, TabPanelNode
from .sphinx.directives import WokwiDirective, WokwiExampleDirective
from .sphinx import html
from sphinx.application import Sphinx


# Configuration defaults with their config keys
# Format: "config_key": default_value
# you can define these using environment variables or in conf.py
# None means that has to be defined externally (does not have a default)
CONFIG_DEFAULTS = {
    "docs_embed_wokwi_viewer_url": "https://wokwi.com/experimental/viewer",
    "docs_embed_default_width": "100%",
    "docs_embed_default_height": "500px",
    "docs_embed_default_allowfullscreen": True,
    "docs_embed_default_loading": "lazy",
    "docs_embed_esp_launchpad_url": "https://espressif.github.io/esp-launchpad",
    "docs_embed_about_wokwi_url": "https://docs.wokwi.com",
    "docs_embed_skip_validation": False,
    "docs_embed_github_base_url": None,  # deduced from Github ENV in CI
    "docs_embed_github_branch": None,  # deduced from Github ENV in CI
    "docs_embed_public_root": None,  # deduced from Github ENV in CI
    "docs_embed_binaries_dir": None,  # deduced from Github ENV in CI
}


def _override_config_from_env(app: Sphinx, config) -> None:
    """Override config values from environment variables if they exist.

    For each config value, checks for an environment variable with the same name in UPPERCASE.
    For example: docs_embed_github_branch -> DOCS_EMBED_GITHUB_BRANCH
    """
    for config_key, config_val in CONFIG_DEFAULTS.items():
        env_var = config_key.upper()
        env_value = os.environ.get(env_var)
        if env_value is None and config_val is None:
            raise RuntimeError(f"Configuration '{config_key}' must be set via environment variable '{env_var}'")

        if env_value is not None:
            # Handle boolean conversion for allowfullscreen
            if config_key == "docs_embed_default_allowfullscreen":
                env_value = env_value.lower() in ("true", "1", "yes", "on")
            setattr(config, config_key, env_value)


def _register_static(app: Sphinx) -> None:
    pkg_static = Path(__file__).parent / "_static"
    if getattr(app.config, "html_static_path", None) is None:
        app.config.html_static_path = []
    if str(pkg_static) not in app.config.html_static_path:
        app.config.html_static_path.append(str(pkg_static))
    app.add_css_file("wokwi_embed.css")
    app.add_js_file("wokwi_embed.js")


def setup(app: Sphinx) -> None:
    # Register all config values with their defaults
    for config_key, default_value in CONFIG_DEFAULTS.items():
        app.add_config_value(config_key, default_value, "env")

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

    app.connect("config-inited", _override_config_from_env)
    app.connect("builder-inited", _register_static)

    return {
        "version": "0.7.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
