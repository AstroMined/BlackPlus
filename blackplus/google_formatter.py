"""
blackplus/google_formatter.py

This module contains the GoogleDocstringFormatter class, which is responsible for
formatting docstrings according to the Google style guide.
"""

import re
import logging
from textwrap import dedent, wrap
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from blackplus.formatter import BaseDocstringFormatter, ASTInfo

# Global flag to enable/disable logging
ENABLE_LOGGING = True

def log_debug(message):
    if ENABLE_LOGGING:
        logging.debug(message)

@dataclass
class DocstringSection:
    name: str
    marker: str


@dataclass
class FormatterConfig:
    style: str
    sections: List[DocstringSection]
    max_line_length: int
    max_summary_length: int


class GoogleDocstringFormatter(BaseDocstringFormatter):
    """
    A class to handle docstring formatting based on user-defined configurations,
    following the Google style guide.
    """

    def __init__(self, config: Dict[str, Any], source_lines: List[str]):
        """
        Initialize the GoogleDocstringFormatter with the provided configuration.

        Args:
            config (Dict[str, Any]): Configuration dictionary for docstring formatting.
            source_lines (List[str]): The source code lines of the file being formatted.
        """
        log_debug(f"__init__ input - config: {type(config)}, {config}, source_lines: {type(source_lines)}, {source_lines[:5]}...")
        super().__init__(config, source_lines)
        self.formatter_config = self._create_formatter_config(config)
        self.current_section = None
        self.section_handlers = {
            "summary": self._format_summary,
            "description": self._format_description,
            "args": self._format_args,
            "attributes": self._format_attributes,
            "returns": self._format_returns,
            "yields": self._format_returns,
            "raises": self._format_raises,
            "example": self._format_examples,
            "examples": self._format_examples,
            "note": self._preserve_indentation,
            "notes": self._preserve_indentation,
        }

    def _create_formatter_config(self, config: Dict[str, Any]) -> FormatterConfig:
        """
        Create a FormatterConfig instance from the provided configuration dictionary.

        Args:
            config (Dict[str, Any]): Configuration dictionary for docstring formatting.

        Returns:
            FormatterConfig: An instance of FormatterConfig.
        """
        log_debug(f"_create_formatter_config input - config: {type(config)}, {config}")
        result = FormatterConfig(
            style=config.get("style", "google"),
            sections=self._get_sections(config),
            max_line_length=config.get("max_line_length", 72),
            max_summary_length=config.get("max_summary_length", 80)
        )
        log_debug(f"_create_formatter_config output - result: {type(result)}, {result}")
        return result

    def _get_sections(self, config: Dict[str, Any]) -> List[DocstringSection]:
        """
        Get the sections configuration based on the selected style.

        Args:
            config (Dict[str, Any]): Configuration dictionary for docstring formatting.

        Returns:
            List[DocstringSection]: List of DocstringSection instances.
        """
        log_debug(f"_get_sections input - config: {type(config)}, {config}")
        default_sections = [
            DocstringSection(name="summary", marker=""),
            DocstringSection(name="description", marker=""),
            DocstringSection(name="args", marker="Args:"),
            DocstringSection(name="returns", marker="Returns:"),
            DocstringSection(name="yields", marker="Yields:"),
            DocstringSection(name="raises", marker="Raises:"),
            DocstringSection(name="attributes", marker="Attributes:"),
            DocstringSection(name="example", marker="Example:"),
            DocstringSection(name="examples", marker="Examples:"),
            DocstringSection(name="note", marker="Note:"),
            DocstringSection(name="notes", marker="Notes:"),
            DocstringSection(name="todo", marker="Todo:"),
        ]

        result = config.get("sections", default_sections)
        log_debug(f"_get_sections output - result: {type(result)}, {result}")
        return result

    def format_docstring(self, docstring: str, ast_info: ASTInfo) -> str:
        """
        Format the given docstring according to the configuration and AST information.

        Args:
            docstring (str): The original docstring to be formatted.
            ast_info (ASTInfo): The extracted AST information.

        Returns:
            str: The formatted docstring.
        """
        log_debug(f"format_docstring input - docstring: {type(docstring)}, {docstring}, ast_info: {type(ast_info)}, {ast_info}")
        cleaned_docstring = self._clean_docstring(docstring)
        lines = self._split_into_lines(cleaned_docstring)
        
        result = self._add_missing_component_placeholders(cleaned_docstring, ast_info)
        lines = self._split_into_lines(result)

        docstring_length = len(lines)

        base_indent = self._get_base_indent(ast_info)
        formatted_sections = self._format_sections(lines, ast_info, docstring_length, base_indent)
        
        result = self._join_formatted_sections(formatted_sections, docstring_length, base_indent)

        log_debug(f"format_docstring output - result: {type(result)}, {result}")
        return result

    def _get_base_indent(self, ast_info: ASTInfo) -> int:
        """
        Determine the base indentation for the docstring based on AST information.

        Args:
            ast_info (ASTInfo): The extracted AST information.

        Returns:
            int: The number of spaces for base indentation.
        """
        log_debug(f"_get_base_indent input - ast_info: {type(ast_info)}, {ast_info}")
        
        # If there are no params, attributes, return type, or raises, assume it's a module-level docstring
        if not ast_info.params and not ast_info.attributes and not ast_info.return_type and not ast_info.raises:
            base_indent = 0
        # If there are params or a return type, assume it's a function or method
        elif ast_info.params or ast_info.return_type:
            base_indent = 4
        # If there are attributes, assume it's a class
        elif ast_info.attributes:
            base_indent = 4
        # Default to 4 spaces for any other case
        else:
            base_indent = 4
        
        log_debug(f"_get_base_indent output - base_indent: {base_indent}")
        return base_indent

    def _join_formatted_sections(self, formatted_sections: List[str], docstring_length: int, base_indent: int) -> str:
        """
        Join formatted sections and add necessary blank lines.

        Args:
            formatted_sections (List[str]): List of formatted docstring sections.
            docstring_length (int): The total number of lines in the original docstring.
            base_indent (int): The base indentation for the docstring.

        Returns:
            str: The joined and formatted docstring.
        """
        log_debug(f"_join_formatted_sections input - formatted_sections: {type(formatted_sections)}, {formatted_sections}, docstring_length: {type(docstring_length)}, {docstring_length}, base_indent: {type(base_indent)}, {base_indent}")
        result = "\n".join(section for section in formatted_sections if section)
        lines = result.split("\n")

        # Remove whitespace from lines that contain only whitespace
        lines = [line if line.strip() else "" for line in lines]

        # Ensure there's a blank line at the end of the docstring
        if lines[-1].strip():
            lines.append("")

        result = "\n".join(lines)

        # Add closing quotes
        if docstring_length == 1:
            initial_indent = " " * base_indent + "    "
            formatted_docstring = f'{initial_indent}"""{result.rstrip()}"""'
        else:
            initial_indent = " " * base_indent
            formatted_docstring = f'{initial_indent}"""{result}\n{initial_indent}"""'

        log_debug(f"_join_formatted_sections output - formatted_docstring: {type(formatted_docstring)}, {formatted_docstring}")
        return formatted_docstring

    def _format_sections(self, lines: List[str], ast_info: ASTInfo, docstring_length: int, base_indent: int) -> List[str]:
        """Format all sections of the docstring."""
        log_debug(f"_format_sections input - lines: {type(lines)}, {lines}, ast_info: {type(ast_info)}, {ast_info}, docstring_length: {type(docstring_length)}, {docstring_length}, base_indent: {type(base_indent)}, {base_indent}")
        formatted_sections = []
        self.current_section = None
        current_content = []

        # Handle summary and description
        if lines:
            summary = self._format_summary([lines[0]])
            formatted_sections.append("\n".join(summary))

            description_end = next((i for i, line in enumerate(lines[1:], 1) if self._identify_section(line)), len(lines))
            if description_end > 1:
                description = self._format_description(lines[1:description_end], self.formatter_config.max_line_length, base_indent)
                formatted_sections.append("\n".join(description))

            lines = lines[description_end:]

        # Handle other sections
        for i, line in enumerate(lines):
            section = self._identify_section(line)
            
            if section and section != self.current_section:
                if self.current_section or current_content:
                    formatted_section = self._format_section(self.current_section, current_content, docstring_length, ast_info, is_last_section=(i == len(lines) - 1), base_indent=base_indent)
                    formatted_sections.append("\n".join(formatted_section) if isinstance(formatted_section, list) else formatted_section)
                self.current_section = section
                current_content = []
            
            current_content.append(line)

        if self.current_section or current_content:
            formatted_section = self._format_section(self.current_section, current_content, docstring_length, ast_info, is_last_section=True, base_indent=base_indent)
            formatted_sections.append("\n".join(formatted_section) if isinstance(formatted_section, list) else formatted_section)

        log_debug(f"_format_sections output - formatted_sections: {type(formatted_sections)}, {formatted_sections}")
        return formatted_sections

    def _identify_section(self, line: str) -> Optional[DocstringSection]:
        """
        Identify the section based on the line content.

        Args:
            line (str): A line from the docstring.

        Returns:
            Optional[DocstringSection]: The identified DocstringSection or None.
        """
        log_debug(f"_identify_section input - line: {type(line)}, {line}")
        stripped_line = line.strip()
        
        for section in self.formatter_config.sections:
            if section.marker and stripped_line == section.marker:
                log_debug(f"_identify_section output - section: {type(section)}, {section}")
                return section
        
        log_debug("_identify_section output - None")
        return None

    def _format_section(self, section: Optional[DocstringSection], content: List[str], docstring_length: int, ast_info: ASTInfo, is_last_section: bool, base_indent: int) -> str:
        """
        Format a section of the docstring.

        Args:
            section (Optional[DocstringSection]): The section configuration.
            content (List[str]): The content of the section.
            docstring_length (int): The total number of lines in the docstring.
            ast_info (ASTInfo): The extracted AST information.
            is_last_section (bool): Whether this is the last section in the docstring.
            base_indent (int): The base indentation for the docstring.

        Returns:
            str: The formatted section.
        """
        log_debug(f"_format_section input - section: {type(section)}, {section}, content: {type(content)}, {content}, docstring_length: {type(docstring_length)}, {docstring_length}, ast_info: {type(ast_info)}, {ast_info}, is_last_section: {type(is_last_section)}, {is_last_section}, base_indent: {type(base_indent)}, {base_indent}")
        if not section:
            result = self._format_description(content, self.formatter_config.max_line_length, base_indent)
            log_debug(f"_format_section output (no section) - result: {type(result)}, {result}")
            return result

        handler = self.section_handlers.get(section.name, self._format_generic_section)
        if section.name in ["args", "attributes", "returns", "yields", "raises"]:
            formatted_content = handler(content, ast_info)
        else:
            formatted_content = handler(content)

        result = self._apply_indentation(formatted_content, section, docstring_length, is_last_section, base_indent)
        log_debug(f"_format_section output - result: {type(result)}, {result}")
        return result

    def _apply_indentation(self, formatted_content: List[str], section: DocstringSection, docstring_length: int, is_last_section: bool, base_indent: int) -> str:
        """Apply indentation to the formatted content."""
        log_debug(f"_apply_indentation input - formatted_content: {type(formatted_content)}, {formatted_content}, section: {type(section)}, {section}, docstring_length: {type(docstring_length)}, {docstring_length}, is_last_section: {type(is_last_section)}, {is_last_section}, base_indent: {type(base_indent)}, {base_indent}")
        formatted_section = self._indent_section_content(formatted_content, section, docstring_length, base_indent)
        result = self._add_section_spacing(formatted_section, section, is_last_section, docstring_length)
        log_debug(f"_apply_indentation output - result: {type(result)}, {result}")
        return result

    def _indent_section_content(self, formatted_content: List[str], section: DocstringSection, docstring_length: int, base_indent: int) -> str:
        """Indent the content of a section."""
        log_debug(f"_indent_section_content input - formatted_content: {type(formatted_content)}, {formatted_content}, section: {type(section)}, {section}, docstring_length: {type(docstring_length)}, {docstring_length}, base_indent: {type(base_indent)}, {base_indent}")
        formatted_section = ""
        indent = " " * base_indent
        for i, line in enumerate(formatted_content):
            if docstring_length == 1:
                formatted_section += f"{line}"
            elif i == 0 and section.name == "summary":
                formatted_section += f"{indent}{line}\n"
            elif section.marker and line == section.marker:
                formatted_section += f"{indent}{line}\n"
            else:
                formatted_section += f"{indent}    {line}\n"
        log_debug(f"_indent_section_content output - formatted_section: {type(formatted_section)}, {formatted_section}")
        return formatted_section

    def _add_section_spacing(self, formatted_section: str, section: DocstringSection, is_last_section: bool, docstring_length: int) -> str:
        """Add appropriate spacing between sections."""
        log_debug(f"_add_section_spacing input - formatted_section: {type(formatted_section)}, {formatted_section}, section: {type(section)}, {section}, is_last_section: {type(is_last_section)}, {is_last_section}, docstring_length: {type(docstring_length)}, {docstring_length}")
        if not is_last_section:
            formatted_section += "\n"
        elif is_last_section and section.name != "summary" and docstring_length > 1:
            formatted_section += "\n"

        if section.name in ["args", "returns", "raises", "attributes", "yields", "example", "examples", "note", "notes"]:
            formatted_section = "\n" + formatted_section + "\n"

        result = formatted_section.rstrip()
        log_debug(f"_add_section_spacing output - result: {type(result)}, {result}")
        return result

    def _condense_summary(self, summary: str) -> str:
        """
        Condense the summary to a single line if it's too long.

        Args:
            summary (str): The original summary.

        Returns:
            str: The condensed summary.
        """
        log_debug(f"_condense_summary input - summary: {type(summary)}, {summary}")
        max_length = self.formatter_config.max_summary_length
        if len(summary) <= max_length:
            log_debug(f"_condense_summary output (unchanged) - summary: {type(summary)}, {summary}")
            return summary
        
        words = summary.split()
        condensed = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 > max_length:
                break
            condensed.append(word)
            current_length += len(word) + 1
        
        result = " ".join(condensed) + "..."
        log_debug(f"_condense_summary output - result: {type(result)}, {result}")
        return result

    def _clean_docstring(self, docstring: str) -> str:
        """Clean and dedent the docstring."""
        log_debug(f"_clean_docstring input - docstring: {type(docstring)}, {docstring}")
        result = dedent(docstring.strip())
        log_debug(f"_clean_docstring output - result: {type(result)}, {result}")
        return result

    def _split_into_lines(self, text: str) -> List[str]:
        """Split text into lines and remove empty lines."""
        log_debug(f"_split_into_lines input - text: {type(text)}, {text}")
        result = [line.strip() for line in text.split("\n") if line.strip()]
        log_debug(f"_split_into_lines output - result: {type(result)}, {result}")
        return result

    def _format_summary(self, content: List[str]) -> List[str]:
        """Format the summary section."""
        log_debug(f"_format_summary input - content: {type(content)}, {content}")
        summary = " ".join(content)
        condensed_summary = self._condense_summary(summary)
        result = [f'{condensed_summary}']
        log_debug(f"_format_summary output - result: {type(result)}, {result}")
        return result

    def _format_description(self, content: List[str], width: int, base_indent: int) -> List[str]:
        """Format the description section."""
        log_debug(f"_format_description input - content: {type(content)}, {content}, width: {type(width)}, {width}")
        formatted_content = []
        indentation_level = base_indent
        for paragraph in content:
            wrapped_lines = wrap(paragraph, width - indentation_level)  # Subtract 4 for indentation
            formatted_content.extend(wrapped_lines)
            formatted_content.append("")  # Add a blank line between paragraphs
        if formatted_content and not formatted_content[-1]:
            formatted_content.pop()  # Remove the last blank line
        indentation = " " * indentation_level
        formatted_content = [f"{indentation}{line}" for line in formatted_content]
        # Add a blank line at the beginning of the description
        formatted_content.insert(0, "")
        log_debug(f"_format_description output - formatted_content: {type(formatted_content)}, {formatted_content}")
        return formatted_content

    def _format_args(self, content: List[str], ast_info: ASTInfo) -> List[str]:
        """Format the args section."""
        log_debug(f"_format_args input - content: {type(content)}, {content}, ast_info: {type(ast_info)}, {ast_info}")
        formatted_args = ["Args:"]  # Add the "Args:" header
        param_descriptions = self._extract_param_descriptions(content, ast_info.params)
        formatted_params = self._format_param_like_section(ast_info.params, param_descriptions)
        formatted_args.extend(formatted_params)
        log_debug(f"_format_args output - formatted_args: {type(formatted_args)}, {formatted_args}")
        return formatted_args

    def _format_attributes(self, content: List[str], ast_info: ASTInfo) -> List[str]:
        """Format the attributes section."""
        log_debug(f"_format_attributes input - content: {type(content)}, {content}, ast_info: {type(ast_info)}, {ast_info}")
        attr_descriptions = self._extract_attr_descriptions(content, ast_info.attributes)
        result = self._format_param_like_section(ast_info.attributes, attr_descriptions)
        # Add the "Attributes:" header
        result.insert(0, "Attributes:")
        log_debug(f"_format_attributes output - result: {type(result)}, {result}")
        return result

    def _format_param_like_section(self, items: Dict[str, str], descriptions: Dict[str, str]) -> List[str]:
        """Format a section that resembles parameters (args or attributes)."""
        log_debug(f"_format_param_like_section input - items: {type(items)}, {items}, descriptions: {type(descriptions)}, {descriptions}")
        formatted_items = []
        for item, item_type in items.items():
            desc = descriptions.get(item, "NEEDS_DOCUMENTED")
            desc_paragraphs = desc.split('\n\n')
            
            first_paragraph = self._clean_description(desc_paragraphs[0])
            
            if item_type and item_type != "Any":
                item_line = f"{item} ({item_type}): {first_paragraph}"
            else:
                item_line = f"{item}: {first_paragraph}"
            
            wrapped_lines = wrap(item_line, self.formatter_config.max_line_length - 8)
            # Indent all lines after the first line
            wrapped_lines = [wrapped_lines[0]] + [f"    {line}" for line in wrapped_lines[1:]]

            formatted_items.extend(wrapped_lines)
            
            for paragraph in desc_paragraphs[1:]:
                formatted_items.append("")
                cleaned_paragraph = self._clean_description(paragraph)
                wrapped_lines = wrap(cleaned_paragraph, self.formatter_config.max_line_length - 12)
                formatted_items.extend(["    " + line for line in wrapped_lines])

        log_debug(f"_format_param_like_section output - formatted_items: {type(formatted_items)}, {formatted_items}")
        return formatted_items

    def _format_raises(self, content: List[str], ast_info: ASTInfo) -> List[str]:
        """Format the raises section."""
        log_debug(f"_format_raises input - content: {type(content)}, {content}, ast_info: {type(ast_info)}, {ast_info}")
        formatted_raises = ["Raises:"]
        for exception in ast_info.raises:
            desc = next((line for line in content if line.startswith(exception)), f"{exception}: NEEDS_DOCUMENTED")
            wrapped_lines = wrap(desc.strip(), self.formatter_config.max_line_length - 8)
            formatted_raises.extend(wrapped_lines)
        log_debug(f"_format_raises output - formatted_raises: {type(formatted_raises)}, {formatted_raises}")
        return formatted_raises

    def _format_returns(self, content: List[str], ast_info: ASTInfo) -> List[str]:
        """Format the returns or yields section."""
        log_debug(f"_format_returns input - content: {type(content)}, {content}, ast_info: {type(ast_info)}, {ast_info}")
        formatted_returns = ["Returns:"]
        if content:
            desc = self._clean_description(" ".join(content[1:]))  # Skip the "Returns:" line
            if ast_info.return_type and ast_info.return_type != "Any":
                return_line = f"{ast_info.return_type}: {desc}"
            else:
                return_line = desc
            wrapped_lines = wrap(return_line, self.formatter_config.max_line_length - 8)
            formatted_returns.extend(wrapped_lines)
        
        log_debug(f"_format_returns output - formatted_returns: {type(formatted_returns)}, {formatted_returns}")
        return formatted_returns

    def _format_generic_section(self, content: List[str]) -> List[str]:
        """Format a generic section."""
        log_debug(f"_format_generic_section input - content: {type(content)}, {content}")
        formatted_content = []
        for line in content:
            wrapped_lines = wrap(line.strip(), self.formatter_config.max_line_length - 8)
            formatted_content.extend(wrapped_lines)
        log_debug(f"_format_generic_section output - formatted_content: {type(formatted_content)}, {formatted_content}")
        return formatted_content

    def _extract_param_descriptions(self, content: List[str], param_info: Dict[str, str]) -> Dict[str, str]:
        """
        Extract parameter descriptions from the docstring content using AST information.

        Args:
            content (List[str]): The content of the Args section.
            param_info (Dict[str, str]): Dictionary of parameter names and types from AST.

        Returns:
            Dict[str, str]: Dictionary of parameter names and their descriptions.
        """
        log_debug(f"_extract_param_descriptions input - content: {type(content)}, {content}, param_info: {type(param_info)}, {param_info}")
        result = self._extract_item_descriptions(content, param_info.keys())
        log_debug(f"_extract_param_descriptions output - result: {type(result)}, {result}")
        return result

    def _extract_attr_descriptions(self, content: List[str], attr_info: Dict[str, str]) -> Dict[str, str]:
        """
        Extract attribute descriptions from the docstring content using AST information.

        Args:
            content (List[str]): The content of the Attributes section.
            attr_info (Dict[str, str]): Dictionary of attribute names and types from AST.

        Returns:
            Dict[str, str]: Dictionary of attribute names and their descriptions.
        """
        log_debug(f"_extract_attr_descriptions input - content: {type(content)}, {content}, attr_info: {type(attr_info)}, {attr_info}")
        result = self._extract_item_descriptions(content, attr_info.keys())
        log_debug(f"_extract_attr_descriptions output - result: {type(result)}, {result}")
        return result

    def _extract_item_descriptions(self, content: List[str], item_names: List[str]) -> Dict[str, str]:
        """
        Extract item descriptions from the docstring content.

        Args:
            content (List[str]): The content of the section.
            item_names (List[str]): List of item names to extract descriptions for.

        Returns:
            Dict[str, str]: Dictionary of item names and their descriptions.
        """
        log_debug(f"_extract_item_descriptions input - content: {type(content)}, {content}, item_names: {type(item_names)}, {item_names}")
        item_descriptions = {}
        current_item = None
        current_desc = []
        in_paragraph = False

        for line in content:
            stripped_line = line.strip()
            item_match = next((item for item in item_names if stripped_line.startswith(item)), None)
            
            if item_match:
                if current_item:
                    item_descriptions[current_item] = '\n\n'.join(current_desc).strip()
                current_item = item_match
                current_desc = [stripped_line[len(item_match):].strip()]
                in_paragraph = True
            elif stripped_line == "":
                if in_paragraph:
                    current_desc.append("")
                    in_paragraph = False
            else:
                if not in_paragraph:
                    current_desc.append("")
                    in_paragraph = True
                current_desc.append(stripped_line)

        if current_item:
            item_descriptions[current_item] = '\n\n'.join(current_desc).strip()

        log_debug(f"_extract_item_descriptions output - item_descriptions: {type(item_descriptions)}, {item_descriptions}")
        return item_descriptions

    def _clean_description(self, description: str) -> str:
        """
        Clean up the description string by removing leading non-alphanumeric characters.

        Args:
            description (str): The original description string.

        Returns:
            str: The cleaned description string.
        """
        log_debug(f"_clean_description input - description: {type(description)}, {description}")
        result = re.sub(r'^[^a-zA-Z0-9]+', '', description).strip()
        log_debug(f"_clean_description output - result: {type(result)}, {result}")
        return result

    def _add_missing_component_placeholders(self, docstring: str, ast_info: ASTInfo) -> str:
        """
        Add placeholders for missing components in the docstring.

        Args:
            docstring (str): The formatted docstring.
            ast_info (ASTInfo): The extracted AST information.

        Returns:
            str: The docstring with added placeholders for missing components.
        """
        log_debug(f"_add_missing_component_placeholders input - docstring: {type(docstring)}, {docstring}, ast_info: {type(ast_info)}, {ast_info}")
        lines = docstring.split("\n")
        
        new_lines = []
        for line in lines:
            new_lines.append(line)
            if any(section.marker in line for section in self.formatter_config.sections if section.marker):
                new_lines.append("")  # Add a blank line after each section marker
        
        components = ["Args", "Returns", "Raises", "Attributes"]
        for component in components:
            if component.lower() not in docstring.lower():
                if component == "Args" and ast_info.params:
                    new_lines.append("")
                    new_lines.append("Args:")
                    for arg, arg_type in ast_info.params.items():
                        new_lines.append(f"    {arg}: NEEDS_DOCUMENTED")
                    new_lines.append("")  # Add a blank line after Args section
                elif component == "Returns" and ast_info.return_type:
                    new_lines.append("")
                    new_lines.append("Returns:")
                    new_lines.append("    NEEDS_DOCUMENTED")
                    new_lines.append("")  # Add a blank line after Returns section
                elif component == "Raises" and ast_info.raises:
                    new_lines.append("")
                    new_lines.append("Raises:")
                    for exception in ast_info.raises:
                        new_lines.append(f"    {exception}: NEEDS_DOCUMENTED")
                    new_lines.append("")  # Add a blank line after Raises section
                elif component == "Attributes" and ast_info.attributes:
                    new_lines.append("")
                    new_lines.append("Attributes:")
                    for attr, attr_type in ast_info.attributes.items():
                        new_lines.append(f"    {attr}: NEEDS_DOCUMENTED")
                    new_lines.append("")  # Add a blank line after Attributes section
        
        # Remove the last blank line if it exists
        if new_lines and not new_lines[-1].strip():
            new_lines.pop()
        
        result = "\n".join(new_lines)
        log_debug(f"_add_missing_component_placeholders output - result: {type(result)}, {result}")
        return result

    def _preserve_indentation(self, content: List[str]) -> List[str]:
        """
        Preserve the indentation of the original content.

        Args:
            content (List[str]): The original content lines.

        Returns:
            List[str]: The content with preserved indentation.
        """
        log_debug(f"_preserve_indentation input - content: {type(content)}, {content}")
        if not content:
            log_debug("_preserve_indentation output - empty list")
            return []

        # Find the minimum indentation
        min_indent = min(len(line) - len(line.lstrip()) for line in content if line.strip())

        # Remove the minimum indentation from all lines
        result = [line[min_indent:] if line.strip() else "" for line in content]
        result.append("")
        log_debug(f"_preserve_indentation output - result: {type(result)}, {result}")
        return result

    def _format_examples(self, content: List[str]) -> List[str]:
        """
        Format the examples section of the docstring.

        Args:
            content (List[str]): The content of the examples section.

        Returns:
            List[str]: The formatted examples section.
        """
        log_debug(f"_format_examples input - content: {type(content)}, {content}")
        formatted_examples = []
        examples_header = content[0]
        in_code_block = False
        code_block_indent = 0
        
        for line in content[1:]:  # Skip the "Examples:" line
            stripped_line = line.strip()
            
            if stripped_line.startswith(">>>") or stripped_line.startswith("..."):
                if not in_code_block:
                    in_code_block = True
                    code_block_indent = len(line) - len(line.lstrip())
                formatted_examples.append(line)
            elif stripped_line.startswith("```") or stripped_line.endswith("```"):
                in_code_block = not in_code_block
                formatted_examples.append(line)
            elif in_code_block:
                # Preserve indentation for code blocks
                formatted_examples.append(line[code_block_indent:])
            else:
                # Wrap text description
                wrapped_lines = wrap(stripped_line, self.formatter_config.max_line_length - 8)
                formatted_examples.extend(wrapped_lines)
            
            if not in_code_block and stripped_line:
                formatted_examples.append("")  # Add a blank line after text description
        
        if formatted_examples and not formatted_examples[-1]:
            formatted_examples.pop()  # Remove the last blank line if it exists

        # Add the Examples: header
        formatted_examples = [examples_header] + formatted_examples

        log_debug(f"_format_examples output - formatted_examples: {type(formatted_examples)}, {formatted_examples}")
        return formatted_examples
