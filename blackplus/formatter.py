"""
blackplus/formatter.py

This module contains the core functionality for the BlackPlus formatter,
including docstring processing and code formatting using black and isort.
"""

import ast
import tempfile
import os
from pathlib import Path
from textwrap import wrap, dedent
from typing import Any, Dict, List, Optional

import black
import isort
# pylint: disable=import-error
import toml


def read_config(config_path: str = "pyproject.toml") -> Dict[str, Any]:
    """
    Read and parse the configuration from pyproject.toml.

    Parameters:
    config_path (str): Path to the pyproject.toml file.

    Returns:
    Dict[str, Any]: Parsed configuration dictionary.
    """
    with open(config_path, "r", encoding="utf-8") as config_file:
        config = toml.load(config_file)
    return config.get("tool", {}).get("blackplus", {})


# pylint: disable=too-few-public-methods
class DocstringFormatter:
    """
    A class to handle docstring formatting based on user-defined configurations.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the DocstringFormatter with the provided configuration.

        Parameters:
        config (Dict[str, Any]): Configuration dictionary for docstring formatting.
        """
        self.config = config.get("docstrings", {})
        self.sections = self.config.get("sections", [])

    def format_docstring(self, docstring: str) -> str:
        """
        Format the given docstring according to the configuration.

        Parameters:
        docstring (str): The original docstring to be formatted.

        Returns:
        str: The formatted docstring.
        """
        lines = docstring.split("\n")
        formatted_sections = []

        current_section = self._identify_section("")  # Start with summary section
        current_content = []

        for line in lines:
            section = self._identify_section(line)
            if section and section != current_section:
                if current_section or current_content:
                    formatted_sections.append(
                        self._format_section(current_section, current_content)
                    )
                current_section = section
                current_content = []
            else:
                current_content.append(line)

        if current_section or current_content:
            formatted_sections.append(
                self._format_section(current_section, current_content)
            )

        result = "\n\n".join(section for section in formatted_sections if section)
        return result.strip()

    def _identify_section(self, line: str) -> Optional[Dict[str, Any]]:
        """
        Identify the section based on the line content.

        Parameters:
        line (str): A line from the docstring.

        Returns:
        Optional[Dict[str, Any]]: The identified section configuration, or None if not found.
        """
        stripped_line = line.strip()
        for section in self.sections:
            if section["marker"] == "" and stripped_line == "":
                return section
            if section["marker"] and stripped_line.startswith(section["marker"]):
                return section
        return None

    def _format_section(self, section: Dict[str, Any], content: List[str]) -> str:
        """
        Format a section of the docstring.

        Parameters:
        section (Dict[str, Any]): The section configuration.
        content (List[str]): The content of the section.

        Returns:
        str: The formatted section.
        """
        if not section:  # Handle case with no identified section
            return "\n".join(line.strip() for line in content if line.strip())

        formatted_content = []
        width = section.get("width", 72)

        if "code_example" in section:
            formatted_content.extend(
                self._format_code_example(content, section["code_example"])
            )
        else:
            for line in content:
                if line.strip():
                    formatted_content.extend(wrap(line.strip(), width=width))
                else:
                    formatted_content.append("")

        section_content = "\n".join(formatted_content).strip()
        if section["marker"]:
            return f"{section['marker']}\n{section_content}"
        return section_content

    def _format_code_example(
        self, content: List[str], code_config: Dict[str, str]
    ) -> List[str]:
        """
        Format a code example within a docstring.

        Parameters:
        content (List[str]): The content of the code example.
        code_config (Dict[str, str]): Configuration for code example formatting.

        Returns:
        List[str]: The formatted code example.
        """
        start_marker = code_config.get("start_marker", "```python")
        end_marker = code_config.get("end_marker", "```")

        code_block = []
        in_code_block = False
        formatted_content = []

        for line in content:
            stripped_line = line.strip()
            if stripped_line == start_marker:
                in_code_block = True
                formatted_content.append(stripped_line)
            elif stripped_line == end_marker:
                in_code_block = False
                formatted_code = self._format_code_snippet("\n".join(code_block))
                formatted_content.extend(formatted_code.split("\n"))
                formatted_content.append(stripped_line)
                code_block = []
            elif in_code_block:
                code_block.append(line)
            else:
                formatted_content.append(line)

        return formatted_content

    def _format_code_snippet(self, code_snippet: str) -> str:
        """
        Format a code snippet using black.

        Parameters:
        code_snippet (str): The code snippet to format.

        Returns:
        str: The formatted code snippet.
        """
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".py", delete=False) as temp_file:
            temp_file.write(dedent(code_snippet))
            temp_file.flush()
            temp_file_path = temp_file.name

        try:
            mode = black.Mode(line_length=88)
            black.format_file_in_place(Path(temp_file_path), fast=False, mode=mode)

            with open(temp_file_path, "r") as formatted_file:
                formatted_code = formatted_file.read()

            # Adjust indentation to match the original code snippet
            original_indent = len(code_snippet) - len(code_snippet.lstrip())
            formatted_lines = [" " * original_indent + line if line.strip() else line
                               for line in formatted_code.splitlines()]
            return "\n".join(formatted_lines)

        except black.NothingChanged:
            return code_snippet
        except black.InvalidInput:
            # Handle code that cannot be parsed
            return code_snippet
        finally:
            os.unlink(temp_file_path)


def run_black(file_path: str, config: Dict[str, Any]) -> None:
    """
    Run black on the specified file.

    Parameters:
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

    Parameters:
    file_path (str): Path to the file to be formatted.
    config (Dict[str, Any]): Configuration for isort.
    """
    isort_config = config.get("isort", {})
    isort.file(file_path, **isort_config)


class DocstringTransformer(ast.NodeTransformer):
    """
    AST transformer to modify docstrings in the parsed code.
    """

    def __init__(self, formatter: DocstringFormatter):
        self.formatter = formatter

    def visit_FunctionDef(self, node):
        """
        Visit a function definition node and format its docstring.

        Parameters:
        node (ast.FunctionDef): The function definition node.

        Returns:
        ast.FunctionDef: The modified function definition node.
        """
        self.generic_visit(node)
        if ast.get_docstring(node):
            docstring = ast.get_docstring(node)
            formatted_docstring = self.formatter.format_docstring(docstring)
            node.body[0] = ast.Expr(ast.Str(formatted_docstring))
        return node

    def visit_ClassDef(self, node):
        """
        Visit a class definition node and format its docstring.

        Parameters:
        node (ast.ClassDef): The class definition node.

        Returns:
        ast.ClassDef: The modified class definition node.
        """
        self.generic_visit(node)
        if ast.get_docstring(node):
            docstring = ast.get_docstring(node)
            formatted_docstring = self.formatter.format_docstring(docstring)
            node.body[0] = ast.Expr(ast.Str(formatted_docstring))
        return node

    visit_AsyncFunctionDef = visit_FunctionDef


def format_file(file_path: str, config: Dict[str, Any]) -> None:
    """
    Format a single file using black, isort, and custom docstring formatting.

    Parameters:
    file_path (str): Path to the file to be formatted.
    config (Dict[str, Any]): Configuration dictionary.
    """
    # Format docstrings
    with open(file_path, "r", encoding="utf-8") as file:
        tree = ast.parse(file.read())

    formatter = DocstringFormatter(config)
    transformer = DocstringTransformer(formatter)
    modified_tree = transformer.visit(tree)

    with open(file_path, "w", encoding="utf-8") as file:
        file.write(ast.unparse(modified_tree))

    # Run black and isort
    run_black(file_path, config)
    run_isort(file_path, config)


def format_files(file_paths: List[str], config: Dict[str, Any]) -> None:
    """
    Format multiple files using black, isort, and custom docstring formatting.

    Parameters:
    file_paths (List[str]): List of file paths to be formatted.
    config (Dict[str, Any]): Configuration dictionary.
    """
    for file_path in file_paths:
        format_file(file_path, config)
