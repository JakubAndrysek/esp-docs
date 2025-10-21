#!/usr/bin/env python3
"""
Diagram and CI synchronization script for ESP32 Arduino examples.
"""

from pathlib import Path
import sys
import rich_click as click
from esp_docs.generic_extensions.docs_embed.tool.wokwi_tool import DiagramSync, target_to_boards


# CLI Commands
@click.group(
    help="docs-embed: Utility to manage Wokwi diagrams and ESP LaunchPad configurations",
    epilog="Run this command from the root of the repository !!!",
)
@click.option(
    "--path",
    required=True,
    type=str,
    help="Path to the directory with examples",
)
@click.pass_context
def main(ctx: click.Context, path: str):
    """Main command group for diagram synchronization tools."""
    ctx.ensure_object(dict)
    ctx.obj["path"] = path


@main.command(name="init-project")
@click.option(
    "--platforms",
    type=str,
    default="esp32,esp32s2,esp32s3",
    help=f"Comma-separated list of platforms to initialise. Valid: {', '.join(target_to_boards.keys())}",
)
@click.option(
    "--diagram/--no-diagram",
    type=bool,
    default=True,
    help="Generate diagram files (default: true)",
)
@click.option(
    "--ci/--no-ci",
    type=bool,
    default=False,
    help="Generate ci.yml from diagrams after creating diagrams (default: false)",
)
@click.option(
    "--override/--no-override",
    type=bool,
    default=False,
    help="Override existing files",
)
@click.pass_context
def init_project(ctx: click.Context, platforms: str, diagram: bool, ci: bool, override: bool):
    """Initialize project scaffolding and optional diagrams/ci.yml.

    Examples:
      docs-embed --path folder/examples init-project --platforms esp32,esp32s2 --diagram --ci --override
    """
    sync = DiagramSync(ctx.obj.get("path"))

    try:
        # parse platforms
        platforms_list = [p.strip() for p in platforms.split(",") if p.strip()]
        allowed = target_to_boards.keys()
        invalid = [p for p in platforms_list if p not in allowed]
        if invalid:
            click.echo(f"Invalid platform(s): {', '.join(invalid)}. Allowed: {', '.join(allowed)}", err=True)
            sys.exit(1)

        sync.init_project(platforms_list, diagram, ci, override)
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
    sync = DiagramSync(ctx.obj.get("path"))

    try:
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
    """Generate diagram files from ci.yml + diagram-default.json.

    Examples:
      docs-embed --path folder/examples diagram-from-ci --platform esp32 --override
    """
    sync = DiagramSync(ctx.obj.get("path"))

    try:
        click.echo("Generating diagram files from ci.yml...")
        sync.generate_diagram_from_ci(platform, override)
        click.echo("Diagram generation completed successfully!")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument(
    "storage_url_prefix",
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
def launchpad_config(
    ctx: click.Context, storage_url_prefix, repo_url_prefix, override
):
    """Generate ESP LaunchPad config file with the specified firmware prefix.

    Examples:
        docs-embed --path folder/examples launchpad-config https://storage.url/prefix --repo-url-prefix https://repo.url/prefix --override
    """
    sync = DiagramSync(ctx.obj.get("path"))

    try:
        click.echo("Generating ESP LaunchPad config...")
        sync.generate_launchpad_config(
            storage_url_prefix, repo_url_prefix, override
        )
        click.echo("ESP LaunchPad config generation completed successfully!")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
