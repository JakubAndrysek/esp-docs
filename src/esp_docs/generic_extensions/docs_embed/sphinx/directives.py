from __future__ import annotations

from typing import List

from docutils import nodes
from docutils.parsers.rst import Directive, directives
from .helpers import css_size, loading_choice
from .nodes import WokwiNode, WokwiTabsNode, TabListNode, TabPanelNode
from os import path


def _get_static_path(self) -> str:
    """Calculate relative path to _static directory from current document."""
    try:
        # Get current document name (e.g., "api/gpio")
        docname = self.state.document.settings.env.docname
        if docname:
            # Count directory levels to go up
            levels_up = len(docname.split("/")) - 1
            if levels_up > 0:
                return "../" * levels_up + "_static/"
        return "_static/"
    except Exception:
        # Fallback to relative path
        return "_static/"


def urljoin(*args) -> str:
    return "/".join(map(lambda x: str(x).rstrip('/'), args))


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

        diagram_url = self.options.get("diagram")
        firmware_url = self.options.get("firmware")
        if not diagram_url or not firmware_url:
            raise self.error("wokwi directive: :diagram: and :firmware: are required (UF2/bin).")

        node = WokwiNode()
        node["iframe_page"] = cfg.docs_embed_wokwi_viewer_url
        node["diagram"] = diagram_url
        node["firmware"] = firmware_url
        node["width"] = self.options.get("width", cfg.docs_embed_default_width)
        node["height"] = self.options.get("height", cfg.docs_embed_default_height)
        node["title"] = self.options.get("title", "Wokwi simulation")
        node["allowfullscreen"] = cfg.docs_embed_default_allowfullscreen if "allowfullscreen" not in self.options else True
        node["loading"] = self.options.get("loading", cfg.docs_embed_default_loading)
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
    Directive to embed Wokwi simulations for Arduino ESP32 examples with multiple targets.

    Usage:
        .. wokwi-example:: libraries/ESP32/examples/GPIO/Blink

    Expected Directory Structure:
        _static/
        └── libraries/ESP32/examples/GPIO/Blink/
            ├── launchpad.toml
            ├── esp32/
            │   ├── Blink.ino.merged.bin
            │   └── diagram.esp32.json
            └── esp32s2/
                ├── Blink.ino.merged.bin
                └── diagram.esp32s2.json


        Arduino Source Files:
        libraries/
        └── ESP32/examples/GPIO/Blink/
            └── Blink.ino
            └── ci.yml

    Configuration (in conf.py):
        TBD

    URL Generation:
        - Firmware: _static/{example_path}/{target}/{sketch_name}.ino.merged.bin
        - Diagram: _static/{example_path}/diagram.{target}.json
        - Launchpad: _static/{example_path}/launchpad.toml

    This directive:
    1. Reads ci.yml from the Arduino example directory to get targets
    2. Creates tabs for each target (ESP32, ESP32-S2, etc.)
    3. Generates URLs for firmware binaries and Wokwi diagrams in _static/
    4. Optionally shows ESP Launchpad button if launchpad.toml exists
    5. Shows source code tab with the .ino file content + link to source
    6. Validates file existence unless docs_embed_skip_validation is True
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
        import yaml

        env = self.state.document.settings.env
        app = env.app
        cfg = app.config

        # Example: libraries/ESP32/examples/GPIO/Blink -> sketch name: Blink
        example_path = self.arguments[0].strip()
        sketch_name = example_path.split("/")[-1]
        docs_embed_esp32_relative_root = "../.."

        docs_embed_public_root = getattr(cfg, "docs_embed_public_root", None)
        if not docs_embed_public_root:
            raise self.error("wokwi-example: 'docs_embed_public_root' must be configured in ENV or conf.py")

        docs_embed_binaries_dir = getattr(cfg, "docs_embed_binaries_dir", None)
        if not docs_embed_binaries_dir:
            raise self.error("wokwi-example: 'docs_embed_binaries_dir' must be configured in ENV or conf.py")
        docs_embed_binaries_dir = path.normpath(docs_embed_binaries_dir)

        # Build path to ci.yml
        ci_yml_path = path.join(env.srcdir, docs_embed_esp32_relative_root, example_path, "ci.yml")
        if not path.isfile(ci_yml_path):
            raise self.error(f"wokwi-example: ci.yml not found at {ci_yml_path}")

        # Load ci.yml
        try:
            with open(ci_yml_path, "r") as f:
                ci_data = yaml.safe_load(f)
        except Exception as e:
            raise self.error(f"wokwi-example: failed to parse ci.yml: {e}")

        # Extract targets
        upload_binary = ci_data.get("upload-binary", {})
        targets = upload_binary.get("targets", [])

        if not targets:
            raise self.error(f"wokwi-example: no targets found in ci.yml at {ci_yml_path}")

        # Get configuration
        skip_validation = getattr(cfg, "docs_embed_skip_validation", False)

        # Create WokwiNode instances for each target
        wokwi_nodes: List[WokwiNode] = []
        for target in targets:
            firmware_path = urljoin(docs_embed_binaries_dir, example_path, target, f"{sketch_name}.ino.merged.bin")
            firmware_url = urljoin(docs_embed_public_root, firmware_path)

            diagram_path = urljoin(docs_embed_binaries_dir, example_path, target, f"diagram.{target}.json")
            diagram_url = urljoin(docs_embed_public_root, diagram_path)

            # Validate files exist (unless skip_validation is set)
            if not skip_validation:
                firmware_full_path = urljoin(env.srcdir, "..", firmware_path)
                if not path.isfile(firmware_full_path):
                    raise self.error(
                        f"wokwi-example: firmware file not found at {firmware_full_path}. "
                        f"Set 'docs_embed_skip_validation = True' in conf.py to bypass this check.")

                diagram_full_path = urljoin(env.srcdir, "..", diagram_path)
                if not path.isfile(diagram_full_path):
                    raise self.error(
                        f"wokwi-example: diagram file not found at {diagram_full_path}. "
                        f"Set 'docs_embed_skip_validation = True' in conf.py to bypass this check.")

            # Create tab label (e.g., "ESP32", "ESP32-S2")
            if target.startswith('esp32'):
                base = target[5:]
                tab_label = f"ESP32-{base.upper()}" if base else "ESP32"
            else:
                tab_label = target.upper()

            # Create WokwiNode
            wn = WokwiNode()
            wn["iframe_page"] = cfg.docs_embed_wokwi_viewer_url
            wn["diagram_url"] = diagram_url
            wn["firmware_url"] = firmware_url
            wn["width"] = self.options.get("width", getattr(cfg, "docs_embed_default_width"))
            wn["height"] = self.options.get("height", getattr(cfg, "docs_embed_default_height"))
            wn["title"] = f"Wokwi simulation — {tab_label}"
            wn["allowfullscreen"] = getattr(cfg, "docs_embed_default_allowfullscreen") if "allowfullscreen" not in self.options else True
            wn["loading"] = self.options.get("loading", getattr(cfg, "docs_embed_default_loading"))
            wn["classes"] = ["wokwi-embed", "from-example"] + self.options.get("class", [])
            wn["static_path"] = _get_static_path(self)

            wn["tab_label"] = tab_label
            wn["suppress_header"] = True  # rendered inside tabs

            wokwi_nodes.append(wn)

        # Now create the tab structure
        code_panels: List[TabPanelNode] = []
        wokwi_panels: List[TabPanelNode] = []

        ino_filename = f"{sketch_name}.ino"
        ino_full_path = path.join(env.srcdir, docs_embed_esp32_relative_root, example_path, ino_filename)
        if path.isfile(ino_full_path):
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

        for i, wn in enumerate(wokwi_nodes):
            panel = TabPanelNode()
            panel["label"] = wn["tab_label"]
            panel["active"] = False
            panel.children = [wn]
            wokwi_panels.append(panel)

        # Combine all panels
        panels = code_panels + wokwi_panels

        # Create tabs structure
        serial = env.new_serialno("wokwi-tabs") if env and hasattr(env, "new_serialno") else id(self)
        root_id = f"wokwi-tabs-{serial}"

        tablist = TabListNode()
        tablist["root_id"] = root_id
        labels = [p.get("label") or f"Tab {i+1}" for i, p in enumerate(panels)]
        tablist["labels"] = labels
        panel_ids = [f"{root_id}-panel-{i}" for i in range(len(panels))]
        tablist["panel_ids"] = panel_ids

        # Separate labels for code and wokwi
        tablist["tabs_code"] = [p.get("label") for p in code_panels]
        tablist["tabs_wokwi"] = [p.get("label") for p in wokwi_panels]

        tablist["static_path"] = _get_static_path(self)

        # Link to ESP Launchpad if launchpad.toml exists (optional)
        launchpad_path = path.join(docs_embed_binaries_dir, example_path, "launchpad.toml")
        launchpad_full_path = path.join(env.srcdir, "..", launchpad_path)
        if path.isfile(launchpad_full_path):
            launchpad_url = urljoin(docs_embed_public_root, launchpad_path)
            launchpad_base_url = getattr(env.app.config, "docs_embed_esp_launchpad_url", "")
            sep = "&" if "?" in launchpad_base_url else "?"
            tablist["launchpad_href"] = f"{launchpad_base_url.rstrip('/')}/{sep}flashConfigURL={launchpad_url}"
            print(f"Launchpad URL: {tablist['launchpad_href']}")

        # Link to GitHub source .ino file
        github_base = getattr(cfg, "docs_embed_github_base_url")
        github_branch = getattr(cfg, "docs_embed_github_branch")
        if github_base and github_branch:
            tablist["github_href"] = urljoin(github_base, "tree", github_branch, example_path, f"{sketch_name}.ino")

        for pid, panel in zip(panel_ids, panels):
            panel["panel_id"] = pid

        tabs_root = WokwiTabsNode()
        tabs_root.children = [tablist] + panels
        if "class" in self.options:
            tabs_root["classes"] = self.options["class"]
        tabs_root["variant"] = "example"

        return [tabs_root]
