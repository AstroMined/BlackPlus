"""
blackplus/formatter.py

This module contains the core functionality for the BlackPlus formatter,
including docstring processing and code formatting using black and isort.
"""

import ast
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Type, Optional, Union

import black
import isort
import toml

@dataclass
class ASTInfo:
    params: Dict[str, str]
    attributes: Dict[str, str]
    return_type: Optional[str]
    raises: List[str]

class BaseDocstringFormatter(ABC):
    """
    Base class for docstring formatters that encapsulates common functionality.
    """

    def __init__(self, config: Dict[str, Any], source_lines: List[str]):
        """
        Initialize the BaseDocstringFormatter.

        Args:
            config (Dict[str, Any]): Configuration dictionary.
            source_lines (List[str]): List of source code lines.
        """
        self.config = config
        self.source_lines = source_lines

    @abstractmethod
    def format_docstring(self, docstring: str, ast_info: ASTInfo) -> str:
        """
        Format the given docstring.

        Args:
            docstring (str): The docstring to format.
            ast_info (ASTInfo): The extracted AST information.

        Returns:
            str: The formatted docstring.
        """
        pass

    def _wrap_paragraph(self, paragraph: str, width: int) -> str:
        """
        Wrap a paragraph to the specified width.

        Args:
            paragraph (str): The paragraph to wrap.
            width (int): The maximum line width.

        Returns:
            str: The wrapped paragraph.
        """
        words = paragraph.split()
        lines = []
        current_line = []

        for word in words:
            if len(' '.join(current_line + [word])) <= width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)

        if current_line:
            lines.append(' '.join(current_line))

        return '\n'.join(lines)

    def _split_into_paragraphs(self, text: Union[str, List[str]]) -> List[str]:
        """
        Split the given text into paragraphs.

        Args:
            text (Union[str, List[str]]): The text to split, either as a string or a list of strings.

        Returns:
            List[str]: List of paragraphs.
        """
        if isinstance(text, str):
            return [p.strip() for p in text.split('\n\n') if p.strip()]
        elif isinstance(text, list):
            paragraphs = []
            current_paragraph = []
            for line in text:
                if line.strip():
                    current_paragraph.append(line.strip())
                elif current_paragraph:
                    paragraphs.append(' '.join(current_paragraph))
                    current_paragraph = []
            if current_paragraph:
                paragraphs.append(' '.join(current_paragraph))
            return paragraphs
        else:
            raise ValueError("Input must be either a string or a list of strings")

    def _clean_description(self, description: str) -> str:
        """
        Clean the description by removing extra whitespace and newlines.

        Args:
            description (str): The description to clean.

        Returns:
            str: The cleaned description.
        """
        return ' '.join(description.split())

    def _extract_ast_info(self, node: ast.AST) -> ASTInfo:
        """
        Extract relevant information from the AST node.

        Args:
            node (ast.AST): The AST node to extract information from.

        Returns:
            ASTInfo: An object containing extracted AST information.
        """
        params = self._get_param_info(node)
        attributes = self._get_attr_info(node)
        return_type = self._get_return_type(node)
        raises = self._get_raises_info(node)
        return ASTInfo(params, attributes, return_type, raises)

    def _get_param_info(self, node: ast.AST) -> Dict[str, str]:
        """
        Extract parameter information from the AST node.

        Args:
            node (ast.AST): The AST node containing the function definition.

        Returns:
            Dict[str, str]: A dictionary of parameter names and their types.
        """
        param_info = {}
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for arg in node.args.args:
                if arg.arg != 'self':
                    param_type = self._get_annotation_str(arg.annotation)
                    param_info[arg.arg] = param_type
        return param_info

    def _get_attr_info(self, node: ast.AST) -> Dict[str, str]:
        """
        Extract attribute information from the AST node.

        Args:
            node (ast.AST): The AST node containing the class definition.

        Returns:
            Dict[str, str]: A dictionary of attribute names and their types.
        """
        attr_info = {}
        if isinstance(node, ast.ClassDef):
            for stmt in node.body:
                if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                    attr_type = self._get_annotation_str(stmt.annotation)
                    attr_info[stmt.target.id] = attr_type
        return attr_info

    def _get_return_type(self, node: ast.AST) -> Optional[str]:
        """
        Extract return type information from the AST node.

        Args:
            node (ast.AST): The AST node containing the function definition.

        Returns:
            Optional[str]: The return type as a string, or None if not specified.
        """
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return self._get_annotation_str(node.returns)
        return None

    def _get_raises_info(self, node: ast.AST) -> List[str]:
        """
        Extract information about raised exceptions from the AST node.

        Args:
            node (ast.AST): The AST node to analyze.

        Returns:
            List[str]: A list of exception names that are raised in the function.
        """
        raises = []
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for stmt in ast.walk(node):
                if isinstance(stmt, ast.Raise):
                    exception_name = self._get_exception_name(stmt.exc)
                    if exception_name:
                        raises.append(exception_name)
        return list(set(raises))  # Remove duplicates

    def _get_annotation_str(self, annotation: Optional[ast.AST]) -> str:
        """
        Convert an AST annotation to a string representation.

        Args:
            annotation (Optional[ast.AST]): The AST annotation node.

        Returns:
            str: The string representation of the annotation, or "Any" if not specified.
        """
        if annotation:
            return ast.unparse(annotation)
        return "Any"

    def _get_exception_name(self, exc: Optional[ast.AST]) -> Optional[str]:
        """
        Extract the exception name from an AST node.

        Args:
            exc (Optional[ast.AST]): The AST node representing an exception.

        Returns:
            Optional[str]: The name of the exception, or None if it couldn't be determined.
        """
        if isinstance(exc, ast.Name):
            return exc.id
        elif isinstance(exc, ast.Call) and isinstance(exc.func, ast.Name):
            return exc.func.id
        return None


class DocstringTransformer(ast.NodeTransformer):
    """
    AST transformer to modify docstrings in the parsed code.
    """

    def __init__(self, formatter: BaseDocstringFormatter):
        self.formatter = formatter

    def _format_docstring(self, node: ast.AST) -> None:
        """
        Format the docstring of the given node.

        Args:
            node (ast.AST): The AST node containing the docstring.
        """
        if ast.get_docstring(node):
            docstring = ast.get_docstring(node)
            ast_info = self.formatter._extract_ast_info(node)
            formatted_docstring = self.formatter.format_docstring(docstring, ast_info)
            node.body[0] = ast.Expr(ast.Str(s=formatted_docstring))

    def visit_Module(self, node: ast.Module) -> ast.Module:
        """
        Visit a module node and format its docstring.

        Args:
            node (ast.Module): The module node.

        Returns:
            ast.Module: The modified module node.
        """
        self.generic_visit(node)
        self._format_docstring(node)
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """
        Visit a function definition node and format its docstring.

        Args:
            node (ast.FunctionDef): The function definition node.

        Returns:
            ast.FunctionDef: The modified function definition node.
        """
        self.generic_visit(node)
        self._format_docstring(node)
        return node

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        """
        Visit a class definition node and format its docstring.

        Args:
            node (ast.ClassDef): The class definition node.

        Returns:
            ast.ClassDef: The modified class definition node.
        """
        self.generic_visit(node)
        self._format_docstring(node)
        return node

    def visit_Assign(self, node: ast.Assign) -> ast.Assign:
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
                ast_info = self.formatter._extract_ast_info(node)
                formatted_docstring = self.formatter.format_docstring(docstring, ast_info)
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
    
    blackplus_config = config.get("tool", {}).get("blackplus", {})
    
    # Set default values for configuration options
    default_config = {
        "style": "google",
        "max_line_length": 88,
        "max_summary_length": 80,
    }
    
    # Update the default configuration with user-specified values
    default_config.update(blackplus_config)
    
    return default_config


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


def get_formatter(style: str, config: Dict[str, Any], source_lines: List[str]) -> BaseDocstringFormatter:
    """
    Factory function to get the appropriate docstring formatter based on the style.

    Args:
        style (str): The desired docstring style (e.g., 'google', 'numpy').
        config (Dict[str, Any]): Configuration dictionary.
        source_lines (List[str]): List of source code lines.

    Returns:
        BaseDocstringFormatter: An instance of the appropriate formatter subclass.

    Raises:
        ValueError: If an unsupported style is specified.
    """
    if style.lower() == 'google':
        from blackplus.google_formatter import GoogleDocstringFormatter
        return GoogleDocstringFormatter(config, source_lines)
    # Add other formatters here as they are implemented
    # elif style.lower() == 'numpy':
    #     from blackplus.numpy_formatter import NumpyDocstringFormatter
    #     return NumpyDocstringFormatter(config, source_lines)
    else:
        raise ValueError(f"Unsupported docstring style: {style}")


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

    # Get the appropriate formatter based on the style
    style = config.get("style", "google")
    formatter = get_formatter(style, config, source_lines)

    # Format docstrings
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
