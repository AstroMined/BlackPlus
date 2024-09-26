"""BlackPlus: Extend Black to format code and docstrings with custom configurations.

This package formats Python code using Black and isort, while also applying
custom formatting to docstrings based on user-defined configurations.
"""

from blackplus.cli import main as cli_main
from blackplus.formatter import (
    format_file,
    format_files,
    read_config,
)

__version__ = "0.1.0"

__all__ = ["format_file", "format_files", "read_config", "cli_main"]
