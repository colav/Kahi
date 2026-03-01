"""CLI entry points for Kahi."""

from __future__ import annotations

import argparse


def run_cli() -> None:
    """Entry point for kahi_run command."""
    parser = argparse.ArgumentParser(description="ETL for bibliographic data.")
    parser.add_argument(
        "--workflow",
        type=str,
        help="Workflow file in YAML format",
        required=True,
    )
    parser.add_argument(
        "--verbose",
        type=int,
        help="Verbosity level from 0 to 5 (0 = no output)",
        default=0,
    )
    parser.add_argument(
        "--log",
        choices=["yes", "no"],
        help="Whether to save logs in the database",
        default="yes",
    )

    args = parser.parse_args()

    from kahi.Kahi import Kahi

    use_log = args.log == "yes"
    kahi = Kahi(args.workflow, verbose=args.verbose, use_log=use_log)
    kahi.run()


def generate_cli() -> None:
    """Entry point for kahi_generate command."""
    parser = argparse.ArgumentParser(description="Generate a Kahi plugin template.")
    parser.add_argument(
        "--plugin",
        type=str,
        required=True,
        help=("Name for the new plugin. Example: --plugin test  →  generates Kahi_test"),
    )

    args = parser.parse_args()

    from kahi.PluginGenerator import PluginGenerator

    generator = PluginGenerator(args.plugin)
    generator.generate()


if __name__ == "__main__":
    run_cli()
