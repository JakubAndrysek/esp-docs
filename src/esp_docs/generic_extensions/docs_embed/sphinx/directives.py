from __future__ import annotations

from typing import List, Optional, Tuple

from docutils import nodes
from docutils.parsers.rst import Directive, directives

from .helpers import css_size, loading_choice, slug_lower
from .nodes import WokwiNode, WokwiTabsNode, TabListNode, TabPanelNode


class WokwiDirective(Directive):
    has_content = False
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = True

    option_spec = {
        "name": directives.unchanged,
        "tab": directives.unchanged,
        "diagram": directives.uri,
        "firmware": directives.uri,
        "width": css_size,
        "height": css_size,
        "title": directives.unchanged,
        "allowfullscreen": directives.flag,
        "loading": loading_choice,
        "class": directives.class_option,
    }

    def run(self):
        env = self.state.document.settings.env
        cfg = env.app.config

        diagram = self.options.get("diagram")
        firmware = self.options.get("firmware")
        if not firmware:
            raise self.error("wokwi directive: :firmware: is required (UF2/bin).")

        node = WokwiNode()
        node["iframe_page"] = cfg.wokwi_viewer_url
        node["diagram"] = diagram
        node["firmware"] = firmware
        node["width"] = self.options.get("width", cfg.wokwi_default_width)
        node["height"] = self.options.get("height", cfg.wokwi_default_height)
        node["title"] = self.options.get("title", "Wokwi simulation")
        node["allowfullscreen"] = cfg.wokwi_default_allowfullscreen if "allowfullscreen" not in self.options else True
        node["loading"] = self.options.get("loading", cfg.wokwi_default_loading)
        node["classes"] = ["wokwi-embed"] + self.options.get("class", [])
        node["suppress_header"] = False

        tab_label = (
            self.options.get("name")
            or self.options.get("tab")
            or (self.arguments[0].strip() if self.arguments else None)
        )
        if tab_label:
            node["tab_label"] = tab_label

        return [node]


class WokwiExampleDirective(Directive):
    """
    Usage:

    .. wokwi-example:: libraries/ESP32/examples/GPIO/BlinkRGB

    This directive:
    1. Looks for ci.json in the specified path relative to docs_embed_root
    2. Reads the targets from ci.json["upload-binary"]["targets"]
    3. Creates tabs for each target (ESP32, ESP32-S2, etc.)
    4. Uses docs_embed_store_prefix + path + /.gen/ to build URLs for firmware and diagrams
    5. Optionally shows ESP Launchpad button if launchpad.toml exists
    6. Adds a link to the source code on GitHub if the example is from arduino-esp32 repo
    """
    required_arguments = 1  # path to example directory
    optional_arguments = 0
    final_argument_whitespace = False

    option_spec = {
        "width": css_size,
        "height": css_size,
        "allowfullscreen": directives.flag,
        "loading": directives.unchanged,
        "class": directives.class_option,
    }

    has_content = False

    def run(self):
        import json
        import os
        from urllib.parse import urljoin

        def _make_url(prefix: Optional[str], path: Optional[str]) -> Optional[str]:
            """Helper to build full URL from prefix and path."""
            if not path:
                return None
            if path.startswith(("http://", "https://")):
                return path
            if not prefix:
                return None
            # Ensure trailing slash on prefix
            if not prefix.endswith("/"):
                prefix = prefix + "/"
            return urljoin(prefix, path.lstrip("/"))

        env = self.state.document.settings.env
        app = env.app
        cfg = app.config

        example_path = self.arguments[0].strip()

        # Get configuration values
        docs_embed_root = getattr(cfg, "docs_embed_root", None)
        docs_embed_store_prefix = getattr(cfg, "docs_embed_store_prefix", None)

        if not docs_embed_root:
            raise self.error("wokwi-example: 'docs_embed_root' must be set in conf.py")
        if not docs_embed_store_prefix:
            raise self.error("wokwi-example: 'docs_embed_store_prefix' must be set in conf.py")

        # Build path to ci.json
        ci_json_path = os.path.join(env.srcdir, docs_embed_root, example_path, "ci.json")

        if not os.path.isfile(ci_json_path):
            raise self.error(f"wokwi-example: ci.json not found at {ci_json_path}")

        # Load ci.json
        try:
            with open(ci_json_path, "r") as f:
                ci_data = json.load(f)
        except Exception as e:
            raise self.error(f"wokwi-example: failed to parse ci.json: {e}")

        # Extract targets
        upload_binary = ci_data.get("upload-binary", {})
        targets = upload_binary.get("targets", [])

        if not targets:
            raise self.error(f"wokwi-example: no targets found in ci.json at {ci_json_path}")

        # Build base URL for generated files
        gen_base_url = _make_url(docs_embed_store_prefix, f"{example_path}/.gen/")

        # Find the .ino file in the example directory
        example_full_path = os.path.join(env.srcdir, docs_embed_root, example_path)
        ino_files = [f for f in os.listdir(example_full_path) if f.endswith('.ino')]

        # Create WokwiNode instances for each target
        wokwi_nodes: List[WokwiNode] = []

        for target in targets:
            # Create tab label (ESP32, ESP32-S2, etc.)
            tab_label = target.upper().replace("ESP", "ESP")

            # Build firmware and diagram URLs
            firmware_url = _make_url(gen_base_url, f"{target}.bin")
            diagram_url = _make_url(gen_base_url, f"diagram.{target}.json")

            # Create WokwiNode
            wn = WokwiNode()
            wn["iframe_page"] = cfg.wokwi_viewer_url
            wn["diagram"] = diagram_url
            wn["firmware"] = firmware_url
            wn["width"] = self.options.get("width", getattr(cfg, "wokwi_default_width", "100%"))
            wn["height"] = self.options.get("height", getattr(cfg, "wokwi_default_height", "500px"))
            wn["title"] = f"Wokwi simulation — {tab_label}"
            wn["allowfullscreen"] = getattr(cfg, "wokwi_default_allowfullscreen", True) if "allowfullscreen" not in self.options else True
            wn["loading"] = self.options.get("loading", getattr(cfg, "wokwi_default_loading", "lazy"))
            wn["classes"] = ["wokwi-embed", "from-example"] + self.options.get("class", [])

            wn["tab_label"] = tab_label
            wn["suppress_header"] = True  # rendered inside tabs
            wn["from_example"] = True

            wokwi_nodes.append(wn)

        # Now create the tab structure similar to WokwiTabsDirective
        code_panels: List[TabPanelNode] = []
        wokwi_panels: List[TabPanelNode] = []

        # Add source code tab first if .ino file exists
        if ino_files:
            ino_filename = ino_files[0]  # Use the first .ino file found

            # Create a literal_block node with the file content
            try:
                ino_full_path = os.path.join(env.srcdir, docs_embed_root, example_path, ino_filename)
                with open(ino_full_path, 'r', encoding='utf-8') as f:
                    source_content = f.read()

                code_block = nodes.literal_block(source_content, source_content)
                code_block['language'] = 'arduino'
                code_block['classes'] = ['highlight']

                # Create source code panel
                source_panel = TabPanelNode()
                source_panel["label"] = ino_filename
                source_panel["active"] = True  # Source code tab is active by default
                source_panel.children = [code_block]
                code_panels.append(source_panel)
            except Exception:
                # If we can't read the file, skip the source code tab
                pass

        for i, wn in enumerate(wokwi_nodes):
            panel = TabPanelNode()
            panel["label"] = wn["tab_label"]
            panel["active"] = (i == 0 and not ino_files)  # First wokwi tab is active only if no source code tab
            panel.children = [wn]
            wokwi_panels.append(panel)

        # Combine all panels
        panels = code_panels + wokwi_panels

        # Create tabs structure
        env = getattr(self.state.document.settings, "env", None)
        serial = env.new_serialno("wokwi-tabs") if env and hasattr(env, "new_serialno") else id(self)
        root_id = f"wokwi-tabs-{serial}"

        tablist = TabListNode()
        tablist["root_id"] = root_id
        labels = [p.get("label") or f"Tab {i+1}" for i, p in enumerate(panels)]
        tablist["labels"] = labels
        panel_ids = [f"{root_id}-panel-{i}" for i in range(len(panels))]
        tablist["panel_ids"] = panel_ids

        # Separate labels for code and wokwi
        tabs_code = [p.get("label") for p in code_panels]
        tabs_wokwi = [p.get("label") for p in wokwi_panels]
        tablist["tabs_code"] = tabs_code
        tablist["tabs_wokwi"] = tabs_wokwi

        # Separate root_ids
        root_id_code = f"{root_id}-code" if tabs_code else None
        root_id_wokwi = f"{root_id}-wokwi" if tabs_wokwi else None
        tablist["root_id_code"] = root_id_code
        tablist["root_id_wokwi"] = root_id_wokwi

        # Always add launchpad support
        launchpad_toml_path = os.path.join(env.srcdir, docs_embed_root, example_path, ".gen/launchpad.toml")
        has_launchpad = os.path.isfile(launchpad_toml_path)

        # Always show launchpad button
        launchpad_base_url = getattr(env.app.config, "wokwi_esp_launchpad_url", "https://espressif.github.io/esp-launchpad/")
        tablist["launchpad_icon"] = getattr(env.app.config, "wokwi_launchpad_icon_url", "")

        if has_launchpad:
            launchpad_toml_url = _make_url(gen_base_url, "launchpad.toml")
            if launchpad_toml_url:
                sep = "&" if "?" in launchpad_base_url else "?"
                tablist["launchpad_href"] = f"{launchpad_base_url.rstrip('/')}/{sep}flashConfigURL={launchpad_toml_url}"
        else:
            # Use base launchpad URL
            tablist["launchpad_href"] = launchpad_base_url.rstrip('/')

        for pid, panel in zip(panel_ids, panels):
            panel["panel_id"] = pid

        tabs_root = WokwiTabsNode()
        tabs_root.children = [tablist] + panels
        if "class" in self.options:
            tabs_root["classes"] = self.options["class"]
        tabs_root["variant"] = "example"

        return [tabs_root]
