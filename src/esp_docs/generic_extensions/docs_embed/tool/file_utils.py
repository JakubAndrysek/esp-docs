"""Utility functions for file operations: loading and saving JSON and YAML files with error handling and formatting."""


from pathlib import Path
import json
import sys
from typing import Any, Dict

import click
import yaml
import tomli_w


def load_json(file_path: Path) -> Dict[str, Any]:
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

def load_yaml(file_path: Path) -> Dict[str, Any]:
	"""Load YAML file safely with error handling."""
	try:
		with open(file_path, 'r', encoding='utf-8') as f:
			return yaml.safe_load(f)
	except FileNotFoundError:
		click.echo(f"Error: File {file_path} not found", err=True)
		sys.exit(1)
	except yaml.YAMLError as e:
		click.echo(f"Error: Invalid YAML in {file_path}: {e}", err=True)
		sys.exit(1)

def save_yaml(file_path: Path, data: Dict[str, Any], override: bool = False) -> None:
	"""Save YAML file with proper formatting."""
	if file_path.exists() and not override:
		click.echo(f"Warning: {file_path} already exists. Use --override to overwrite.")
		return

	file_path.parent.mkdir(parents=True, exist_ok=True)
	try:
		with open(file_path, 'w', encoding='utf-8') as f:
			yaml.safe_dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
	except Exception as e:
		click.echo(f"Error: Failed to write YAML to {file_path}: {e}", err=True)
		sys.exit(1)

	click.echo(f"Saved: {file_path}")

def save_json(file_path: Path, data: Dict[str, Any], override: bool = False) -> None:
	"""Save JSON file with compact formatting."""
	if file_path.exists() and not override:
		click.echo(f"Warning: {file_path} already exists. Use --override to overwrite.")
		return

	file_path.parent.mkdir(parents=True, exist_ok=True)
	try:
		with open(file_path, 'w', encoding='utf-8') as f:
			json.dump(data, f, indent=2, ensure_ascii=False, separators=(',', ': '))
	except Exception as e:
		click.echo(f"Error: Failed to write JSON to {file_path}: {e}", err=True)
		sys.exit(1)

	click.echo(f"Saved: {file_path}")

def save_toml(file_path: Path, data: Dict[str, Any], override: bool = False) -> None:
	"""Save TOML file with proper formatting."""
	if file_path.exists() and not override:
		click.echo(f"Warning: {file_path} already exists. Use --override to overwrite.")
		return

	file_path.parent.mkdir(parents=True, exist_ok=True)
	try:
		with open(file_path, 'wb') as f:
			tomli_w.dump(data, f)
	except Exception as e:
		click.echo(f"Error: Failed to write TOML to {file_path}: {e}", err=True)
		sys.exit(1)

	click.echo(f"Saved: {file_path}")