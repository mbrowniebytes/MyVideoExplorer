#!/usr/bin/env python3
"""Thin launcher that delegates startup to MyVideoExplorer.app.app_main.run()."""

import sys

from MyVideoExplorer.app.app_main import run


def main() -> int:
    """Entry point for the application."""
    return run()


if __name__ == "__main__":
    sys.exit(run())
