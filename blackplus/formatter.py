"""
blackplus/formatter.py

This module contains the core functionality for the BlackPlus formatter,
including docstring processing and code formatting using black and isort.
"""

import ast
from pathlib import Path
from typing import Any, Dict, List

import black
import isort
import toml

from blackplus.google_formatter import GoogleDocstringFormatter


class DocstringTransformer(ast.NodeTransformer):
    """
    AST transformer to modify docstrings in the parsed code.
    """

    def __init__(self, formatter: GoogleDocstringFormatter):
        self.formatter = formatter

    def visit_Module(self, node):
        """
        Visit a module node and format its docstring.

        Args:
            node (ast.Module): The module node.

        Returns:
            ast.Module: The modified module node.
        """
        self.generic_visit(node)
        if ast.get_docstring(node):
            docstring = ast.get_docstring(node)
            formatted_docstring = self.formatter.format_docstring(docstring, node)
            node.body[0] = ast.Expr(ast.Str(s=formatted_docstring))
        return node

    def visit_FunctionDef(self, node):
        """
        Visit a function definition node and format its docstring.

        Args:
            node (ast.FunctionDef): The function definition node.

        Returns:
            ast.FunctionDef: The modified function definition node.
        """
        self.generic_visit(node)
        if ast.get_docstring(node):
            docstring = ast.get_docstring(node)
            formatted_docstring = self.formatter.format_docstring(docstring, node)
            node.body[0] = ast.Expr(ast.Str(s=formatted_docstring))
        return node

    def visit_ClassDef(self, node):
        """
        Visit a class definition node and format its docstring.

        Args:
            node (ast.ClassDef): The class definition node.

        Returns:
            ast.ClassDef: The modified class definition node.
        """
        self.generic_visit(node)
        if ast.get_docstring(node):
            docstring = ast.get_docstring(node)
            formatted_docstring = self.formatter.format_docstring(docstring, node)
            node.body[0] = ast.Expr(ast.Str(s=formatted_docstring))
        return node

    def visit_Assign(self, node):
        """
        Visit an assignment node and format its docstring if it's a variable with a docstring.

        Args:
            node (ast.Assign): The assignment node.

        Returns:
            ast.Assign: The modified assignment node.
        """
        self.generic_visit(node)
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            if (isinstance(node.value, ast.Constant) and
                isinstance(node.value.value, str) and
                len(node.value.value.split('\n')) > 1):  # Multi-line string, likely a docstring
                docstring = node.value.value
                formatted_docstring = self.formatter.format_docstring(docstring, node)
                node.value = ast.Str(s=formatted_docstring)
        return node

    visit_AsyncFunctionDef = visit_FunctionDef


def read_config(config_path: str = "pyproject.toml") -> Dict[str, Any]:
    """
    Read and parse the configuration from pyproject.toml.

    Args:
        config_path (str): Path to the pyproject.toml file.

    Returns:
        Dict[str, Any]: Parsed configuration dictionary.
    """
    with open(config_path, "r", encoding="utf-8") as config_file:
        config = toml.load(config_file)
    return config.get("tool", {}).get("blackplus", {})


def run_black(file_path: str, config: Dict[str, Any]) -> None:
    """
    Run black on the specified file.

    Args:
        file_path (str): Path to the file to be formatted.
        config (Dict[str, Any]): Configuration for black.
    """
    black_config = config.get("black", {})
    line_length = black_config.get("line_length", 88)
    target_version = black_config.get("target_version", ["py38"])

    mode = black.Mode(
        line_length=line_length,
        target_versions={black.TargetVersion[v.upper()] for v in target_version},
    )

    black.format_file_in_place(Path(file_path), fast=False, mode=mode)


def run_isort(file_path: str, config: Dict[str, Any]) -> None:
    """
    Run isort on the specified file.

    Args:
        file_path (str): Path to the file to be formatted.
        config (Dict[str, Any]): Configuration for isort.
    """
    isort_config = config.get("isort", {})
    isort.file(file_path, **isort_config)


def format_file(file_path: str, config: Dict[str, Any]) -> None:
    """
    Format a single file using black, isort, and custom docstring formatting.

    Args:
        file_path (str): Path to the file to be formatted.
        config (Dict[str, Any]): Configuration dictionary.
    """
    # Read the file content
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
        source_lines = content.splitlines()

    # Parse the AST
    tree = ast.parse(content)

    # Format docstrings
    formatter = GoogleDocstringFormatter(config, source_lines)
    transformer = DocstringTransformer(formatter)
    modified_tree = transformer.visit(tree)

    # Write the modified AST back to the file
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(ast.unparse(modified_tree))

    # Run black and isort
    run_black(file_path, config)
    run_isort(file_path, config)


def format_files(file_paths: List[str], config: Dict[str, Any]) -> None:
    """
    Format multiple files using black, isort, and custom docstring formatting.

    Args:
        file_paths (List[str]): List of file paths to be formatted.
        config (Dict[str, Any]): Configuration dictionary.
    """
    for file_path in file_paths:
        format_file(file_path, config)
