#!/usr/bin/env python3
"""
Diagram and CI synchronization script for ESP32 Arduino examples.
"""

import sys
import click
from esp_docs.generic_extensions.docs_embed.tool.wokwi_tool import (
    DiagramSync,
    target_to_boards,
)


# CLI Commands
@click.group(
    help="docs-embed: Utility to manage Wokwi diagrams and ESP LaunchPad configurations"
)
@click.option(
    "--path",
    default=".",
    type=str,
    help="Path to the directory with examples",
)
@click.pass_context
def main(ctx: click.Context, path: str):
    """Main command group for diagram synchronization tools."""
    ctx.ensure_object(dict)
    ctx.obj["path"] = path


@main.command(name="init-diagram")
@click.option(
    "--platforms",
    type=str,
    required=True,
    help=f"Comma-separated list of platforms to initialise. Valid: {', '.join(target_to_boards.keys())}",
)
@click.option(
    "--override/--no-override",
    type=bool,
    default=False,
    help="Override existing files",
)
@click.pass_context
def init_project(ctx: click.Context, platforms: str, override: bool):
    """Initialize a new project with Wokwi diagrams and CI configuration.

    Examples:
      docs-embed init-project --platforms esp32,esp32s2 (generates diagrams for esp32 and esp32s2)
      docs-embed --path folder/examples init-project --platforms esp32,esp32s2 --override
    """
    try:
        sync = DiagramSync(ctx.obj.get("path"))
        platforms_list = [p.strip() for p in platforms.split(",") if p.strip()]
        allowed = target_to_boards.keys()
        invalid = [p for p in platforms_list if p not in allowed]
        if invalid:
            click.echo(
                f"Invalid platform(s): {', '.join(invalid)}. Allowed: {', '.join(allowed)}",
                err=True,
            )
            sys.exit(1)

        sync.init_project(platforms_list, override)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option(
    "--platform",
    help="Specific platform to process (e.g., esp32, esp32s2, esp32s3)",
)
@click.option(
    "--override/--no-override",
    default=False,
    help="Override existing files",
)
@click.pass_context
def ci_from_diagram(ctx: click.Context, platform, override):
    """Generate ci.yml from diagram files."""
    try:
        sync = DiagramSync(ctx.obj.get("path"))
        click.echo("Generating ci.yml from diagram files...")
        sync.generate_ci_from_diagram(platform, override)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option(
    "--platform",
    help="Specific platform to process (e.g., esp32, esp32s2, esp32s3)",
)
@click.option(
    "--override/--no-override",
    default=False,
    help="Override existing files",
)
@click.pass_context
def diagram_from_ci(ctx: click.Context, platform, override):
    """Generate diagram files from ci.yml.

    Examples:
      docs-embed --path folder/examples diagram-from-ci --platform esp32 --override
    """
    try:
        sync = DiagramSync(ctx.obj.get("path"))
        click.echo("Generating diagram files from ci.yml...")
        sync.generate_diagram_from_ci(platform, override)
        click.echo("Diagram generation completed successfully!")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option(
    "--storage_url_prefix",
    type=str,
    required=True,
    envvar="STORAGE_URL_PREFIX",
)
@click.option(
    "--repo_url_prefix",
    type=str,
    required=True,
    envvar="REPO_URL_PREFIX",
    help="URL prefix for the repository when generating LaunchPad config",
)
@click.option(
    "--override/--no-override",
    default=False,
    help="Override existing files",
)
@click.pass_context
def launchpad_config(ctx: click.Context, storage_url_prefix, repo_url_prefix, override):
    """Generate ESP LaunchPad config file with the specified firmware prefix.

    Examples:
        docs-embed --path folder/examples launchpad-config --storage_url_prefix https://storage.url/prefix --repo-url-prefix https://repo.url/prefix --override
    """
    try:
        sync = DiagramSync(ctx.obj.get("path"))
        click.echo("Generating ESP LaunchPad config...")
        sync.generate_launchpad_config(storage_url_prefix, repo_url_prefix, override)
        click.echo("ESP LaunchPad config generation completed successfully!")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
