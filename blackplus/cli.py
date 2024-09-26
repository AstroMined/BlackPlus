"""
blackplus/cli.py

This module provides the command-line interface for the BlackPlus formatter.
"""

import argparse
import logging
import os
import sys
from typing import List

from blackplus.formatter import format_files, read_config


def setup_logging():
    """
    Set up logging configuration for BlackPlus.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments for BlackPlus.

    Returns:
    argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="BlackPlus: A Python code and docstring formatter"
    )
    parser.add_argument("paths", nargs="+", help="Files or directories to format")
    parser.add_argument(
        "--config",
        default="pyproject.toml",
        help="Path to the configuration file (default: pyproject.toml)",
    )
    return parser.parse_args()


def get_python_files(paths: List[str]) -> List[str]:
    """
    Recursively find all Python files in the given paths.

    Parameters:
    paths (List[str]): List of file or directory paths.

    Returns:
    List[str]: List of Python file paths.
    """
    python_files = []
    for path in paths:
        if os.path.isfile(path) and path.endswith(".py"):
            python_files.append(path)
        elif os.path.isdir(path):
            for root, _, files in os.walk(path):
                for file in files:
                    if file.endswith(".py"):
                        python_files.append(os.path.join(root, file))
    return python_files


def main():
    """
    Main entry point for the BlackPlus CLI.
    """
    setup_logging()
    args = parse_arguments()

    try:
        config = read_config(args.config)
    except FileNotFoundError:
        logging.error("Configuration file not found: %s", args.config)
        sys.exit(1)
    except (IOError, ValueError) as e:
        logging.error("Error reading configuration file: %s", str(e))
        sys.exit(1)

    python_files = get_python_files(args.paths)

    if not python_files:
        logging.warning("No Python files found in the specified paths.")
        sys.exit(0)

    logging.info("Found %d Python files to format.", len(python_files))

    try:
        format_files(python_files, config)
        logging.info("Formatting completed successfully.")
    except (IOError, OSError) as e:
        logging.error("An error occurred during file I/O: %s", str(e))
        sys.exit(1)
    except ValueError as e:
        logging.error("An error occurred during formatting: %s", str(e))
        sys.exit(1)
    # pylint: disable=broad-except
    except Exception as e:
        logging.error("An unexpected error occurred: %s", str(e))
        logging.debug("Error details:", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
