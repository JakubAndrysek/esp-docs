#!/usr/bin/env python3
"""
Diagram and CI synchronization script for ESP32 Arduino examples.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import rich_click as click
import requests
import os

from .file_upload import FileWithProgressAndHash

target_to_boards = {
    'esp32': 'board-esp32-devkit-c-v4',
    'esp32c3': 'board-esp32-c3-devkitm-1',
    'esp32c6': 'board-esp32-c6-devkitc-1',
    'esp32h2': 'board-esp32-h2-devkitm-1',
    'esp32p4': 'board-esp32-p4-function-ev',
    'esp32s2': 'board-esp32-s2-devkitm-1',
    'esp32s3': 'board-esp32-s3-devkitc-1',
}


class DiagramSync:
    """Main class for synchronizing diagram files with CI configuration."""

    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        if not self.base_path.exists():
            raise FileNotFoundError(f"Base path {self.base_path} does not exist")
        if not self.base_path.is_dir():
            raise NotADirectoryError(f"Base path {self.base_path} is not a directory")

        self.gen_path = self.base_path / ".gen"
        self.gen_path.mkdir(exist_ok=True)

        self.serial_connections = [
            ["esp:RX", "$serialMonitor:TX", "", []],
            ["esp:TX", "$serialMonitor:RX", "", []]
        ]

        # Default diagram configuration
        self.default_diagram_config = {
            'version': 1,
            'author': 'Espressif Systems',
            'editor': 'wokwi',
            'parts': [],
            'dependencies': {}
        }

    def init_project(self, platforms_list: List[str], diagram: bool, ci: bool, override: bool):
        click.echo(f"Initializing project in {self.base_path}")

        if diagram:
            for platform in platforms_list:
                click.echo(f"Generating diagram for platform: {platform}")
                self.generate_diagram(platform, override)

    def load_json(self, file_path: Path) -> Dict[str, Any]:
        """Load JSON file safely with error handling."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            click.echo(f"Error: File {file_path} not found", err=True)
            sys.exit(1)
        except json.JSONDecodeError as e:
            click.echo(f"Error: Invalid JSON in {file_path}: {e}", err=True)
            sys.exit(1)

    def save_json(self, file_path: Path, data: Dict[str, Any], override: bool = False) -> None:
        """Save JSON file with compact formatting."""
        if file_path.exists() and not override:
            click.echo(f"Warning: {file_path} already exists. Use --override to overwrite.")
            return

        file_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            # Try to use compact-json for better formatting
            from compact_json import Formatter
            formatter = Formatter()
            formatter.dump(data, file_path, newline_at_eof=True)
        except ImportError:
            # Fall back to standard json
            click.echo("compact-json not available, using standard JSON formatting")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, separators=(',', ': '))

        click.echo(f"Saved: {file_path}")

    # Data Processing
    def is_serial_connection(self, connection: List[str]) -> bool:
        """Return True if in the connection is a serial monitor connection."""
        return connection[:3] in [conn[:3] for conn in self.serial_connections]

    def filter_parts(self, parts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out board parts from diagram parts."""
        return [part for part in parts if not part.get("type", "").startswith("board-")]

    def filter_connections(self, connections: List[List[str]]) -> List[List[str]]:
        """Filter out serial monitor connections."""
        return [conn for conn in connections if not self.is_serial_connection(conn)]

    def get_platforms_from_ci(self) -> List[str]:
        """Get all platforms from ci.json targets."""
        ci_file = self.base_path / "ci.json"
        if not ci_file.exists():
            return []

        ci_data = self.load_json(ci_file)
        return ci_data.get("upload-binary", {}).get("targets", [])

    def get_platforms_from_diagrams(self) -> List[str]:
        """Get all platforms from existing diagram files."""
        platforms = []
        for file_path in self.gen_path.glob("diagram.*.json"):
            if file_path.name.startswith("diagram.") and file_path.name.endswith(".json"):
                platform = file_path.name.replace("diagram.", "").replace(".json", "")
                if platform != "default":
                    platforms.append(platform)
        return platforms

    # Diagram Generation
    def create_default_diagram(self, platform: str) -> Dict[str, Any]:
        """Create default diagram with platform-specific pin handling."""
        # Special case for esp32p4
        if platform == 'esp32p4':
            rx_pin = '38'
            tx_pin = '37'
        else:
            rx_pin = 'RX'
            tx_pin = 'TX'

        diagram = self.default_diagram_config.copy()
        diagram['connections'] = [
            [f'esp:{tx_pin}', '$serialMonitor:RX', '', []],
            [f'esp:{rx_pin}', '$serialMonitor:TX', '', []]
        ]

        board_type = target_to_boards.get(platform)
        if not board_type:
            raise ValueError(f"Unknown platform '{platform}' for board mapping or the board is not supported.")

        diagram['parts'] = [{
            "type": board_type,
            "id": "esp",
            "top": 0,
            "left": 0,
            "attrs": {}
        }]
        return diagram

    def platform_to_chipset(self, platform: str) -> str:
        """Convert platform name to ESP LaunchPad chipset format."""
        if platform == 'esp32':
            return 'ESP32'
        elif platform.startswith('esp32'):
            base = platform[5:]  # Remove 'esp32' prefix
            if len(base) == 2:  # e.g., 's3', 'c3', 'h2', 'p4'
                return f'ESP32-{base.upper()}'
        raise ValueError(f"Unknown platform '{platform}' for chipset mapping.")

    # Main Generation Methods
    def generate_ci_from_diagram(self, platform: Optional[str] = None, override: bool = False) -> None:
        """Generate ci.json from diagram files."""
        platforms = [platform] if platform else self.get_platforms_from_diagrams()

        if not platforms:
            click.echo("No diagram files found to process")
            return

        # Load existing ci.json if it exists
        ci_file = self.base_path / "ci.json"
        ci_data = {}
        if ci_file.exists():
            ci_data = self.load_json(ci_file)
            if ci_data.get("upload-binary") and not override:
                click.echo("ci.json already has 'upload-binary' section. Use --override to overwrite.")

        # Ensure upload-binary structure exists in ci_data
        if "upload-binary" not in ci_data:
            ci_data["upload-binary"] = {}

        upload_binary = ci_data["upload-binary"]
        upload_binary["targets"] = upload_binary.get("targets", [])
        upload_binary["diagram"] = upload_binary.get("diagram", {})

        # Process each platform
        for plat in platforms:
            # Add platform to targets if not already present
            if plat not in upload_binary["targets"]:
                upload_binary["targets"].append(plat)

            diagram_file = self.gen_path / f"diagram.{plat}.json"
            if not diagram_file.exists():
                click.echo(f"- {plat}: Warning: diagram.{plat}.json not found, skipping")
                continue

            diagram_data = self.load_json(diagram_file)

            # Build platform-specific diagram
            parts = self.filter_parts(diagram_data.get("parts", []))
            connections = self.filter_connections(diagram_data.get("connections", []))
            dependencies = diagram_data.get("dependencies")

            # Skip platforms with no meaningful content (empty parts and connections)
            if not parts and not connections and not dependencies:
                click.echo(f"- {plat}: Skipping platform {plat}: no parts, connections, or dependencies")
                continue

            platform_diagram = {
                "parts": parts,
                "connections": connections
            }

            # Add dependencies if they exist
            if dependencies:
                platform_diagram["dependencies"] = dependencies

            # Update platform data
            upload_binary["diagram"][plat] = platform_diagram

            click.echo(f"- {plat}: Processed platform: {plat} with {len(platform_diagram['parts'])} parts and {len(platform_diagram['connections'])} connections")

        # Ensure the modified upload_binary is saved back to ci_data
        ci_data["upload-binary"] = upload_binary
        self.save_json(ci_file, ci_data, True)

    def generate_diagram_from_ci(self, platform: Optional[str] = None, override: bool = False) -> None:
        """Generate diagram files from ci.json + diagram-default.json."""
        platforms = [platform] if platform else self.get_platforms_from_ci()

        if not platforms:
            click.echo("No platforms found in ci.json")
            return

        # Load ci.json
        ci_file = self.base_path / "ci.json"
        if not ci_file.exists():
            click.echo("Error: ci.json not found", err=True)
            return

        ci_data = self.load_json(ci_file)

        # Process each platform
        for plat in platforms:
            self.generate_diagram(plat, override, ci_data.get("upload-binary", {}))

    def generate_diagram(self, platform: str, override: bool = False, config_data: Optional[Dict[str, Any]] = {}) -> None:
        diagram_file = self.gen_path / f"diagram.{platform}.json"

        # Check if file exists and we're not overriding
        if diagram_file.exists() and not override:
            click.echo(f"Warning: diagram.{platform}.json already exists. Use --override to overwrite.")
            return

        platform_diagram = config_data.get("diagram", {}).get(platform, {})

        # Start with default diagram for this platform
        diagram_data = self.create_default_diagram(platform)

        # Add platform-specific parts
        if platform_parts := platform_diagram.get("parts"):
            diagram_data["parts"].extend(platform_parts)

        # Add platform-specific connections
        if platform_connections := platform_diagram.get("connections"):
            existing_connections = diagram_data.get("connections", [])
            diagram_data["connections"] = existing_connections + platform_connections

        # Add dependencies if they exist
        if platform_dependencies := platform_diagram.get("dependencies"):
            diagram_data["dependencies"] = platform_dependencies

        self.save_json(diagram_file, diagram_data, True)

    def generate_launchpad_config(self, storage_url_prefix: str, repo_url_prefix: str, override: bool = False) -> None:
        """Generate ESP LaunchPad config file from ci.json targets."""
        project_name = self.base_path.name
        storage_url_prefix = storage_url_prefix.rstrip('/')
        repo_url_prefix = repo_url_prefix.rstrip('/')

        config_file = self.gen_path / "launchpad.toml"
        if config_file.exists() and not override:
            click.echo(f"Warning: {config_file} already exists. Use --override to overwrite.")
            return

        # Load ci.json to get platforms
        ci_file = self.base_path / "ci.json"
        if not ci_file.exists():
            click.echo("Error: ci.json not found", err=True)
            return

        ci_data = self.load_json(ci_file)
        platforms = ci_data.get("upload-binary", {}).get("targets", [])

        if not platforms:
            click.echo("No platforms found in ci.json")
            return

        # Convert platforms to chipsets
        chipsets = [self.platform_to_chipset(platform) for platform in platforms]

        # Check if README.md exists
        readme_file = self.base_path / "README.md"
        config_readme_url = None
        if readme_file.exists():
            config_readme_url = f"{repo_url_prefix}/{self.base_path}/README.md"
            click.echo(f"- Found README.md, will link as: {config_readme_url}")

        # Generate config content
        config_lines = [
            'esp_toml_version = 1.0',
            '',
            f'firmware_images_url = "{storage_url_prefix}"',
            '',
            '# Apps that you support and for which the binaries are available to publish.',
            f'supported_apps = ["{project_name}"]',
            ''
        ]

        if config_readme_url:
            config_lines.extend([f'config_readme_url = "{config_readme_url}"'])

        # Add image configurations for each platform
        for platform in platforms:
            chipset = self.platform_to_chipset(platform)
            lowercase_chipset = chipset.lower()
            binary_name = f"{project_name}-{lowercase_chipset}.bin"
            config_lines.append(f'image.{lowercase_chipset} = "{binary_name}"')

        # Extract description from ci.json if available
        description = ci_data.get("upload-binary", {}).get("description")
        if description:
            click.echo(f"- Found description in ci.json: {description}")
            config_lines.extend([f'description = "{description}"',])

        with open(config_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(config_lines) + '\n')

        click.echo(f"Generated ESP LaunchPad config: {config_file}")
        click.echo(f"Supported chipsets: {', '.join(chipsets)}")
