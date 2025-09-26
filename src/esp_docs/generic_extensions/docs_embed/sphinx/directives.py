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


class WokwiTabsDirective(Directive):
    has_content = True
    option_spec = {
        "json-prefix": directives.uri,
        "width": css_size,
        "height": css_size,
        "allowfullscreen": directives.flag,
        "loading": loading_choice,
        "class": directives.class_option,
        "title": directives.unchanged,
    }

    def _gather_children(self) -> List[nodes.Node]:
        container = nodes.Element()
        self.state.nested_parse(self.content, self.content_offset, container)
        return list(container.children)

    def _collect_panels(
        self, children: List[nodes.Node], json_prefix: Optional[str]
    ) -> Tuple[List[TabPanelNode], List[nodes.system_message]]:
        errors: List[nodes.system_message] = []
        panels: List[TabPanelNode] = []

        def make_panel(label: str, content_nodes: List[nodes.Node], active: bool) -> TabPanelNode:
            panel = TabPanelNode()
            panel["label"] = label
            panel["active"] = active
            panel.children = content_nodes
            return panel

        i = 0
        while i < len(children):
            cur = children[i]

            if isinstance(cur, WokwiNode):
                label = cur.get("tab_label") or cur.get("title") or f"Wokwi {len(panels)+1}"
                panels.append(make_panel(label, [cur], active=(len(panels) == 0)))
                i += 1
                continue

            if isinstance(cur, nodes.target) and cur.get("names"):
                label = cur["names"][0]
                j = i + 1
                while j < len(children) and isinstance(children[j], nodes.target):
                    j += 1
                if j >= len(children):
                    errors.append(self.state_machine.reporter.error(
                        f"wokwi-tabs: target '{label}' has no following content node.",
                        line=self.lineno,
                    ))
                    break
                content = children[j]
                panels.append(make_panel(label, [content], active=(len(panels) == 0)))
                i = j + 1
                continue

            if isinstance(cur, nodes.literal_block):
                label = f"Code {len([p for p in panels if p.get('label', '').startswith('Code')]) + 1}"
                panels.append(make_panel(label, [cur], active=(len(panels) == 0)))
                i += 1
                continue

            i += 1

        json_prefix_local = json_prefix or getattr(self.state.document.settings.env.app.config, "wokwi_json_prefix", None)
        if json_prefix_local:
            json_prefix_local = json_prefix_local.rstrip("/")

        for idx, panel in enumerate(panels, start=1):
            if len(panel.children) == 1 and isinstance(panel.children[0], WokwiNode):
                wn: WokwiNode = panel.children[0]
                if not wn.get("firmware"):
                    errors.append(self.state_machine.reporter.error(
                        f"wokwi-tabs: child #{idx} is missing required :firmware: URL.",
                        line=self.lineno,
                    ))
                if not wn.get("diagram") and json_prefix_local:
                    slug = slug_lower(panel.get("label") or wn.get("tab_label") or f"wokwi-{idx}")
                    wn["diagram"] = f"{json_prefix_local}/diagram-{slug}.json"
                # Inside tabs -> ensure no inner header
                wn["suppress_header"] = True

        return panels, errors

    def run(self):
        if not self.content:
            return []

        raw_children = self._gather_children()
        json_prefix = self.options.get("json-prefix")

        panels, errors = self._collect_panels(raw_children, json_prefix)
        if not panels:
            errors.append(self.state_machine.reporter.error(
                "wokwi-tabs: no child blocks found. Add '.. wokwi::', '.. wokwi-toml::', '.. code-block::', or '.. literalinclude::' with :name:",
                line=self.lineno,
            ))
        if errors:
            return errors

        # Apply tabs-level overrides to Wokwi children
        for p in panels:
            for ch in p.children:
                if isinstance(ch, WokwiNode):
                    if "width" in self.options:
                        ch["width"] = self.options["width"]
                    if "height" in self.options:
                        ch["height"] = self.options["height"]
                    if "loading" in self.options:
                        ch["loading"] = self.options["loading"]
                    if "allowfullscreen" in self.options:
                        ch["allowfullscreen"] = True
                    if "class" in self.options:
                        ch["classes"] = list(dict.fromkeys(ch.get("classes", []) + self.options["class"]))

        # Determine if this tabset was produced from a wokwi-toml block
        from_toml = False
        toml_url: Optional[str] = None
        for p in panels:
            for ch in p.children:
                if isinstance(ch, WokwiNode) and ch.get("from_toml"):
                    from_toml = True
                    if not toml_url and ch.get("toml_url"):
                        toml_url = ch["toml_url"]

        env = getattr(self.state.document.settings, "env", None)
        serial = env.new_serialno("wokwi-tabs") if env and hasattr(env, "new_serialno") else id(self)
        root_id = f"wokwi-tabs-{serial}"

        tablist = TabListNode()
        tablist["root_id"] = root_id
        labels = [p.get("label") or f"Tab {i+1}" for i, p in enumerate(panels)]
        tablist["labels"] = labels
        panel_ids = [f"{root_id}-panel-{i}" for i in range(len(panels))]
        tablist["panel_ids"] = panel_ids

        # Variant: TOML
        if from_toml:
            tablist["variant"] = "toml"
            # Build Launchpad link if we have an http(s) TOML URL
            base = getattr(env.app.config, "wokwi_esp_launchpad_base", "https://espressif.github.io/esp-launchpad/")
            if toml_url:
                sep = "&" if "?" in base else "?"
                tablist["launchpad_href"] = f"{base.rstrip('/')}/{sep}flashConfigURL={toml_url}"
            tablist["launchpad_icon"] = getattr(
                env.app.config,
                "wokwi_launchpad_icon_url",
                "https://raw.githubusercontent.com/espressif/esp-launchpad/24bb22db7e4d6b2182e054d2f482532511c60475/assets/esp_launchpad.svg",
            )

        for pid, panel in zip(panel_ids, panels):
            panel["panel_id"] = pid

        tabs_root = WokwiTabsNode()
        tabs_root.children = [tablist] + panels
        if "class" in self.options:
            tabs_root["classes"] = self.options["class"]
        if from_toml:
            tabs_root["variant"] = "toml"

        return [tabs_root]


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
            diagram_url = _make_url(gen_base_url, f"diagram-{target}.json")

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
        panels: List[TabPanelNode] = []

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
                panels.append(source_panel)
            except Exception:
                # If we can't read the file, skip the source code tab
                pass

        for i, wn in enumerate(wokwi_nodes):
            panel = TabPanelNode()
            panel["label"] = wn["tab_label"]
            panel["active"] = (i == 0 and not ino_files)  # First wokwi tab is active only if no source code tab
            panel.children = [wn]
            panels.append(panel)

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

        # Set variant to "example" and add launchpad support
        tablist["variant"] = "example"

        # Always add launchpad support (check if launchpad.toml exists)
        launchpad_toml_path = os.path.join(env.srcdir, docs_embed_root, example_path, "launchpad.toml")
        has_launchpad = os.path.isfile(launchpad_toml_path)

        # Always show launchpad button with base URL
        base = getattr(env.app.config, "wokwi_esp_launchpad_base", "https://espressif.github.io/esp-launchpad/")
        if has_launchpad:
            launchpad_toml_url = _make_url(gen_base_url, "launchpad.toml")
            if launchpad_toml_url:
                sep = "&" if "?" in base else "?"
                tablist["launchpad_href"] = f"{base.rstrip('/')}/{sep}flashConfigURL={launchpad_toml_url}"
        else:
            # Use base launchpad URL without specific config
            tablist["launchpad_href"] = base.rstrip('/')

        tablist["launchpad_icon"] = getattr(
            env.app.config,
            "wokwi_launchpad_icon_url",
            "https://raw.githubusercontent.com/espressif/esp-launchpad/24bb22db7e4d6b2182e054d2f482532511c60475/assets/esp_launchpad.svg",
        )

        # Store chip information for each panel to build chip-specific launchpad URLs
        tablist["chip_info"] = []
        for target in targets:
            chip_name = target.lower()  # esp32, esp32s2, esp32s3
            tablist["chip_info"].append(chip_name)

        for pid, panel in zip(panel_ids, panels):
            panel["panel_id"] = pid

        tabs_root = WokwiTabsNode()
        tabs_root.children = [tablist] + panels
        if "class" in self.options:
            tabs_root["classes"] = self.options["class"]
        tabs_root["variant"] = "example"

        return [tabs_root]
