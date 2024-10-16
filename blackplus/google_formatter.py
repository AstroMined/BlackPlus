import ast
import re
from textwrap import dedent, wrap
from typing import Any, Dict, List, Optional, Tuple


class GoogleDocstringFormatter:
    """
    A class to handle docstring formatting based on user-defined configurations.
    """

    def __init__(self, config: Dict[str, Any], source_lines: List[str]):
        """
        Initialize the DocstringFormatter with the provided configuration.

        Args:
            config (Dict[str, Any]): Configuration dictionary for docstring formatting.
            source_lines (List[str]): The source code lines of the file being formatted.
        """
        print("DEBUG: Initializing GoogleDocstringFormatter")
        self.config = config.get("docstrings", {})
        self.style = self.config.get("style", "google")
        self.sections = self._get_sections()
        self.source_lines = source_lines
        self.current_section = None
        print(f"DEBUG: Initialization complete. Style: {self.style}")

    def _get_sections(self) -> List[Dict[str, Any]]:
        """
        Get the sections configuration based on the selected style.

        Returns:
            List[Dict[str, Any]]: List of section configurations.
        """
        print("DEBUG: Getting sections configuration")
        default_sections = [
            {"name": "summary", "marker": ""},
            {"name": "description", "marker": ""},
            {"name": "args", "marker": "Args:"},
            {"name": "returns", "marker": "Returns:"},
            {"name": "yields", "marker": "Yields:"},
            {"name": "raises", "marker": "Raises:"},
            {"name": "attributes", "marker": "Attributes:"},
            {"name": "example", "marker": "Example:"},
            {"name": "examples", "marker": "Examples:"},
            {"name": "note", "marker": "Note:"},
            {"name": "notes", "marker": "Notes:"},
            {"name": "todo", "marker": "Todo:"},
        ]

        sections = self.config.get("sections", default_sections)
        print(f"DEBUG: Sections configuration: {sections}")
        return sections

    def _wrap_paragraph(self, paragraph: str, width: int) -> List[str]:
        """
        Wrap a paragraph to the specified width.

        Args:
            paragraph (str): The paragraph to wrap.
            width (int): The maximum width for wrapping.

        Returns:
            List[str]: The wrapped paragraph as a list of lines.
        """
        print(f"DEBUG: Wrapping paragraph. Width: {width}")
        words = paragraph.split()
        lines = []
        current_line = words[0]

        for word in words[1:]:
            if len(current_line) + len(word) + 1 <= width:
                current_line += " " + word
            else:
                lines.append(current_line)
                current_line = word

        lines.append(current_line)
        print(f"DEBUG: Wrapped paragraph: {lines}")
        return lines

    def _split_into_paragraphs(self, content: List[str]) -> List[List[str]]:
        """
        Split the content into paragraphs.

        Args:
            content (List[str]): The content to split.

        Returns:
            List[List[str]]: A list of paragraphs, where each paragraph is a list of lines.
        """
        print("DEBUG: Splitting content into paragraphs")
        paragraphs = []
        current_paragraph = []
        print(f"DEBUG: Content:\n{content}")
        for line in content:
            if line.strip():
                current_paragraph.append(line.strip())
            elif current_paragraph:
                paragraphs.append(current_paragraph)
                current_paragraph = []
        if current_paragraph:
            paragraphs.append(current_paragraph)
        print(f"DEBUG: Paragraphs:\n{paragraphs}")
        return paragraphs

    def format_docstring(self, docstring: str, node: ast.AST) -> str:
        """
        Format the given docstring according to the configuration and node context.

        Args:
            docstring (str): The original docstring to be formatted.
            node (ast.AST): The AST node containing the docstring.

        Returns:
            str: The formatted docstring.
        """
        print("DEBUG: Starting docstring formatting")
        # Remove leading/trailing whitespace and dedent
        cleaned_docstring = dedent(docstring.strip())
        
        # Split into lines and remove empty lines
        lines = [line.strip() for line in cleaned_docstring.split("\n") if line.strip()]
        
        # Add placeholders for missing components
        result = self._add_missing_component_placeholders(cleaned_docstring, node)
        
        # Re-split the result into lines after adding placeholders
        lines = [line.strip() for line in result.split("\n") if line.strip()]

        docstring_length = len(lines)
        print(f"DEBUG: Docstring length: {docstring_length}")

        formatted_sections = []
        self.current_section = None
        current_content = []

        # Add quotes and ensure proper indentation
        base_indent = self._get_base_indent(node)
        print(f"DEBUG: Base indent: '{base_indent}'")
        
        for i, line in enumerate(lines):
            section, line_content = self._identify_section(line, node, i == 0)
            
            if section and section != self.current_section:
                if self.current_section or current_content:
                    formatted_sections.append(
                        self._format_section(self.current_section, current_content, base_indent, docstring_length, node, is_last_section=(i == len(lines) - 1))
                    )
                self.current_section = section
                current_content = []
            
            current_content.extend(line_content)

        if self.current_section or current_content:
            formatted_sections.append(
                self._format_section(self.current_section, current_content, base_indent, docstring_length, node, is_last_section=True)
            )

        result = "\n".join(section for section in formatted_sections if section)

        # Ensure there's a blank line after the summary
        lines = result.split("\n")
        if len(lines) > 1:
            lines.insert(1, "")

        # Ensure there's a blank line between description and other sections
        description_end = next((i for i, line in enumerate(lines) if line.strip().startswith("Attributes:") or line.strip().startswith("Args:")), len(lines))
        if description_end > 2:  # Only add if there's content after the summary
            lines.insert(description_end, "")

        # Ensure there's a blank line at the end of the docstring
        if lines[-1].strip():
            lines.append("")

        result = "\n".join(lines)

        # Add closing quotes
        if docstring_length == 1:
            print("DEBUG: Single-line docstring")
            print(f"DEBUG: Result before formatting: {result}")
            formatted_docstring = f'{result.rstrip()}"""'
        else:
            formatted_docstring = f'{result}\n{base_indent}"""'

        print(f"DEBUG: Formatted docstring:\n{formatted_docstring}")
        return formatted_docstring

    def _identify_section(self, line: str, node: ast.AST, is_first_line: bool) -> Tuple[Optional[Dict[str, Any]], List[str]]:
        """
        Identify the section based on the line content and node context.

        Args:
            line (str): A line from the docstring.
            node (ast.AST): The AST node containing the docstring.
            is_first_line (bool): Whether this is the first line of the docstring.

        Returns:
            Tuple[Optional[Dict[str, Any]], List[str]]: The identified section configuration and initial content.
        """
        print(f"DEBUG: Identifying section for line: {line}")
        stripped_line = line.strip()
        
        # Check if we're already in the Examples or Notes section
        if self.current_section and self.current_section["name"] in ["examples", "example", "notes", "note"]:
            # Check if we've encountered a new section marker
            for section in self.sections:
                if section["marker"] and stripped_line == section["marker"]:
                    print(f"DEBUG: New section identified: {section['name']}")
                    return section, []
            # If not, this line is part of the current section
            print(f"DEBUG: Line is part of current section: {self.current_section['name']}")
            return self.current_section, [stripped_line]
        
        # Check for section markers
        for section in self.sections:
            if section["marker"] and stripped_line == section["marker"]:
                print(f"DEBUG: Section identified by marker: {section['name']}")
                return section, []
        
        # If no specific section is identified, it's either summary, description, or part of the current section
        summary_section = next((section for section in self.sections if section["name"] == "summary"), {"name": "summary", "marker": ""})
        description_section = next((section for section in self.sections if section["name"] == "description"), {"name": "description", "marker": ""})
        
        if is_first_line:
            print("DEBUG: First line identified as summary")
            return summary_section, [stripped_line]
        elif self.current_section:
            if self.current_section["name"] in ["args", "attributes", "raises", "returns", "yields"]:
                print(f"DEBUG: Line is part of current section: {self.current_section['name']}")
                return self.current_section, [stripped_line]
            else:
                print("DEBUG: Line identified as description")
                return description_section, [stripped_line]
        else:
            print("DEBUG: Line identified as description")
            return description_section, [stripped_line]

    def _format_section(self, section: Dict[str, Any], content: List[str], base_indent: str, docstring_length: int, node: ast.AST, is_last_section: bool) -> str:
        """
        Format a section of the docstring.

        Args:
            section (Dict[str, Any]): The section configuration.
            content (List[str]): The content of the section.
            base_indent (str): The base indentation for the docstring.
            docstring_length (int): The total number of lines in the docstring.
            node (ast.AST): The AST node containing the docstring.
            is_last_section (bool): Whether this is the last section in the docstring.

        Returns:
            str: The formatted section.
        """
        print(f"DEBUG: Formatting section: {section['name'] if section else 'None'}")
        if not section:  # Handle case with no identified section
            return "\n".join(content)

        formatted_content = []
        width = self.config.get("max_line_length", 72)

        if section["marker"]:
            formatted_content.append(section["marker"])
        
        if section["name"] == "summary":
            summary = " ".join(content)
            condensed_summary = self._condense_summary(summary)
            formatted_content.append(f'"""{condensed_summary}')
            if docstring_length > 1:
                formatted_content.append("")  # Add a blank line after the summary only for multi-line docstrings
        elif section["name"] == "description":
            paragraphs = self._split_into_paragraphs(content)
            for i, paragraph in enumerate(paragraphs):
                if i > 0:
                    formatted_content.append("")  # Add blank line between paragraphs
                print(f"DEBUG: Paragraph:\n{paragraph}")
                paragraph_text = " ".join(paragraph)
                print(f"DEBUG: Paragraph text:\n{paragraph_text}")
                wrapped_lines = self._wrap_paragraph(paragraph_text, width - len(base_indent))
                print(f"DEBUG: Wrapped lines:\n{wrapped_lines}")
                formatted_content.extend(wrapped_lines)
        elif section["name"] == "args":
            param_info = self._get_param_info(node)
            formatted_params = self._format_args(content, param_info, width)
            formatted_content.extend(formatted_params)
        elif section["name"] == "attributes":
            attr_info = self._get_attr_info(node)
            formatted_attrs = self._format_attributes(content, attr_info, width)
            formatted_content.extend(formatted_attrs)
        elif section["name"] in ["raises"]:
            for line in content:
                wrapped_lines = self._wrap_paragraph(line.strip(), width - 8)
                formatted_content.extend(wrapped_lines)
        elif section["name"] in ["returns", "yields"]:
            return_type = self._get_return_type(node)
            formatted_returns = self._format_returns(content, return_type, width)
            formatted_content.extend(formatted_returns)
        elif section["name"] in ["examples", "example", "notes", "note"]:
            formatted_content.extend(self._preserve_indentation(content))
        else:
            for line in content:
                wrapped_lines = self._wrap_paragraph(line.strip(), width - 4)
                formatted_content.extend(wrapped_lines)

        formatted_section = ""
        for i, line in enumerate(formatted_content):
            if docstring_length == 1:
                formatted_section += f"{base_indent}{line}"
            elif i == 0 and section["name"] == "summary":
                formatted_section += f"{base_indent}{line}\n"
            elif section["marker"] and line == section["marker"]:
                formatted_section += f"{base_indent}{line}\n"
            elif section["name"] == "description":
                formatted_section += f"{base_indent}{line}\n"
            elif section["name"] in ["examples", "example", "notes", "note"]:
                if line.strip():
                    formatted_section += f"{base_indent}    {line}\n"
                else:
                    formatted_section += f"{base_indent}\n"
            else:
                formatted_section += f"{base_indent}    {line}\n"

        # Ensure there's a blank line after each section except the last one
        if not is_last_section:
            formatted_section += f"{base_indent}\n"
        elif is_last_section and section["name"] != "summary" and docstring_length > 1:
            # Add a blank line at the end of the docstring for multi-line docstrings
            print("DEBUG: Adding blank line at the end of the docstring")
            formatted_section += f"{base_indent}\n"

        # Add an extra newline after the description section
        if section["name"] == "description" and not is_last_section:
            formatted_section += f"{base_indent}\n"

        print(f"DEBUG: Formatted section:\n{formatted_section}")
        return formatted_section.rstrip()

    def _preserve_indentation(self, content: List[str]) -> List[str]:
        """
        Preserve the original indentation of the content.

        Args:
            content (List[str]): The content to preserve.

        Returns:
            List[str]: The content with preserved indentation.
        """
        print("DEBUG: Preserving indentation")
        preserved_content = []
        for line in content:
            if line.strip():
                preserved_content.append(line)
            else:
                preserved_content.append("")
        print(f"DEBUG: Preserved content:\n{preserved_content}")
        return preserved_content

    def _condense_summary(self, summary: str) -> str:
        """
        Condense the summary to a single line if it's too long.

        Args:
            summary (str): The original summary.

        Returns:
            str: The condensed summary.
        """
        print(f"DEBUG: Condensing summary: {summary}")
        max_length = self.config.get("max_summary_length", 80)
        if len(summary) <= max_length:
            return summary
        
        words = summary.split()
        condensed = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 > max_length - 3:  # -3 for the ellipsis
                break
            condensed.append(word)
            current_length += len(word) + 1
        
        condensed_summary = " ".join(condensed) + "..."
        print(f"DEBUG: Condensed summary: {condensed_summary}")
        return condensed_summary

    def _format_args(self, content: List[str], param_info: Dict[str, str], width: int) -> List[str]:
        """
        Format argument descriptions using AST information.

        Args:
            content (List[str]): The content of the Args section.
            param_info (Dict[str, str]): Dictionary of parameter names and types from AST.
            width (int): The maximum line width for wrapping.

        Returns:
            List[str]: Formatted argument descriptions.
        """
        print("DEBUG: Formatting args")
        formatted_args = []
        param_descriptions = self._extract_param_descriptions(content, param_info)

        for param, param_type in param_info.items():
            desc = param_descriptions.get(param, "NEEDS_DOCUMENTED")
            desc_paragraphs = desc.split('\n\n')
            
            # Clean the first paragraph
            first_paragraph = self._clean_description(desc_paragraphs[0])
            
            if param_type and param_type != "Any":
                param_line = f"{param} ({param_type}): {first_paragraph}"
            else:
                param_line = f"{param}: {first_paragraph}"
            
            wrapped_lines = self._wrap_paragraph(param_line, width - 8)
            formatted_args.append(wrapped_lines[0])
            for line in wrapped_lines[1:]:
                formatted_args.append("    " + line)
            
            # Process additional paragraphs
            for paragraph in desc_paragraphs[1:]:
                formatted_args.append("")  # Add a blank line between paragraphs
                cleaned_paragraph = self._clean_description(paragraph)
                wrapped_lines = self._wrap_paragraph(cleaned_paragraph, width - 12)  # Extra indentation for continuation
                formatted_args.extend(["    " + line for line in wrapped_lines])

        print(f"DEBUG: Formatted args:\n{formatted_args}")
        return formatted_args

    def _get_return_type(self, node: ast.AST) -> Optional[str]:
        print("DEBUG: Getting return type")
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.returns:
                return_type = ast.unparse(node.returns)
                print(f"DEBUG: Return type: {return_type}")
                return return_type
        print("DEBUG: No return type found")
        return None

    def _format_returns(self, content: List[str], return_type: Optional[str], width: int) -> List[str]:
        print("DEBUG: Formatting returns")
        formatted_returns = []
        if content:
            desc = self._clean_description(content[0])
            if return_type:
                return_line = f"{return_type}: {desc}"
            else:
                return_line = desc
            wrapped_lines = self._wrap_paragraph(return_line, width - 8)
            formatted_returns.extend(wrapped_lines)

            # Process additional paragraphs
            for paragraph in content[1:]:
                formatted_returns.append("")  # Add a blank line between paragraphs
                cleaned_paragraph = self._clean_description(paragraph)
                wrapped_lines = self._wrap_paragraph(cleaned_paragraph, width - 8)
                formatted_returns.extend(["    " + line for line in wrapped_lines])
        
        print(f"DEBUG: Formatted returns:\n{formatted_returns}")
        return formatted_returns

    def _format_attributes(self, content: List[str], attr_info: Dict[str, str], width: int) -> List[str]:
        """
        Format attribute descriptions using AST information.

        Args:
            content (List[str]): The content of the Attributes section.
            attr_info (Dict[str, str]): Dictionary of attribute names and types from AST.
            width (int): The maximum line width for wrapping.

        Returns:
            List[str]: Formatted attribute descriptions.
        """
        print("DEBUG: Formatting attributes")
        formatted_attrs = []
        attr_descriptions = self._extract_attr_descriptions(content, attr_info)

        for attr, attr_type in attr_info.items():
            desc = attr_descriptions.get(attr, "NEEDS_DOCUMENTED")
            desc_paragraphs = desc.split('\n\n')
            
            # Clean the first paragraph
            first_paragraph = self._clean_description(desc_paragraphs[0])
            
            if attr_type and attr_type != "Any":
                attr_line = f"{attr} ({attr_type}): {first_paragraph}"
            else:
                attr_line = f"{attr}: {first_paragraph}"
            
            wrapped_lines = self._wrap_paragraph(attr_line, width - 8)
            formatted_attrs.extend(wrapped_lines)
            
            # Process additional paragraphs
            for paragraph in desc_paragraphs[1:]:
                formatted_attrs.append("")  # Add a blank line between paragraphs
                cleaned_paragraph = self._clean_description(paragraph)
                wrapped_lines = self._wrap_paragraph(cleaned_paragraph, width - 8)
                formatted_attrs.extend(["    " + line for line in wrapped_lines])

        print(f"DEBUG: Formatted attributes:\n{formatted_attrs}")
        return formatted_attrs

    def _extract_param_descriptions(self, content: List[str], param_info: Dict[str, str]) -> Dict[str, str]:
        """
        Extract parameter descriptions from the docstring content using AST information.

        Args:
            content (List[str]): The content of the Args section.
            param_info (Dict[str, str]): Dictionary of parameter names and types from AST.

        Returns:
            Dict[str, str]: Dictionary of parameter names and their descriptions.
        """
        print("DEBUG: Extracting parameter descriptions")
        param_descriptions = {}
        current_param = None
        current_desc = []
        in_paragraph = False

        for line in content:
            stripped_line = line.strip()
            param_match = next((param for param in param_info.keys() if stripped_line.startswith(param)), None)
            
            if param_match:
                if current_param:
                    param_descriptions[current_param] = '\n\n'.join(current_desc).strip()
                current_param = param_match
                current_desc = [stripped_line[len(param_match):].strip()]
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

        if current_param:
            param_descriptions[current_param] = '\n\n'.join(current_desc).strip()

        print(f"DEBUG: Extracted parameter descriptions:\n{param_descriptions}")
        return param_descriptions

    def _extract_attr_descriptions(self, content: List[str], attr_info: Dict[str, str]) -> Dict[str, str]:
        """
        Extract attribute descriptions from the docstring content using AST information.

        Args:
            content (List[str]): The content of the Attributes section.
            attr_info (Dict[str, str]): Dictionary of attribute names and types from AST.

        Returns:
            Dict[str, str]: Dictionary of attribute names and their descriptions.
        """
        print("DEBUG: Extracting attribute descriptions")
        attr_descriptions = {}
        current_attr = None
        current_desc = []
        in_paragraph = False

        for line in content:
            stripped_line = line.strip()
            attr_match = next((attr for attr in attr_info.keys() if stripped_line.startswith(attr)), None)
            
            if attr_match:
                if current_attr:
                    attr_descriptions[current_attr] = '\n\n'.join(current_desc).strip()
                current_attr = attr_match
                current_desc = [stripped_line[len(attr_match):].strip()]
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

        if current_attr:
            attr_descriptions[current_attr] = '\n\n'.join(current_desc).strip()

        print(f"DEBUG: Extracted attribute descriptions:\n{attr_descriptions}")
        return attr_descriptions

    def _clean_description(self, desc: str) -> str:
        """
        Clean up the description string by removing leading non-alphanumeric characters.

        Args:
            desc (str): The original description string.

        Returns:
            str: The cleaned description string.
        """
        print(f"DEBUG: Cleaning description: {desc}")
        cleaned = re.sub(r'^[^a-zA-Z0-9]+', '', desc).strip()
        print(f"DEBUG: Cleaned description: {cleaned}")
        return cleaned

    def _get_param_info(self, node: ast.AST) -> Dict[str, str]:
        """
        Extract parameter information from the AST node.

        Args:
            node (ast.AST): The AST node containing the function definition.

        Returns:
            Dict[str, str]: A dictionary of parameter names and their types.
        """
        print("DEBUG: Getting parameter info")
        param_info = {}
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for arg in node.args.args:
                if arg.arg != 'self':
                    param_type = "Any"
                    if arg.annotation:
                        param_type = ast.unparse(arg.annotation)
                    param_info[arg.arg] = param_type
        print(f"DEBUG: Parameter info: {param_info}")
        return param_info

    def _get_attr_info(self, node: ast.AST) -> Dict[str, str]:
        """
        Extract attribute information from the AST node.

        Args:
            node (ast.AST): The AST node containing the class definition.

        Returns:
            Dict[str, str]: A dictionary of attribute names and their types.
        """
        print("DEBUG: Getting attribute info")
        attr_info = {}
        if isinstance(node, ast.ClassDef):
            for stmt in node.body:
                if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                    attr_type = "Any"
                    if stmt.annotation:
                        attr_type = ast.unparse(stmt.annotation)
                    attr_info[stmt.target.id] = attr_type
        print(f"DEBUG: Attribute info: {attr_info}")
        return attr_info

    def _get_base_indent(self, node: ast.AST) -> str:
        """
        Get the base indentation based on the node context.

        Args:
            node (ast.AST): The AST node containing the docstring.

        Returns:
            str: The base indentation.
        """
        print("DEBUG: Getting base indent")
        if isinstance(node, ast.Module):
            return ""
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            indent = self._determine_indent_from_source(node)
            return indent + "    "
        elif isinstance(node, ast.ClassDef):
            return self._determine_indent_from_source(node)
        else:
            return self._determine_indent_from_source(node)

    def _determine_indent_from_source(self, node: ast.AST) -> str:
        """
        Determine the indentation from the source code.

        Args:
            node (ast.AST): The AST node containing the docstring.

        Returns:
            str: The determined indentation.
        """
        print("DEBUG: Determining indent from source")
        if hasattr(node, 'lineno'):
            line_number = node.lineno - 1
            if 0 <= line_number < len(self.source_lines):
                line = self.source_lines[line_number]
                indent = len(line) - len(line.lstrip())
                print(f"DEBUG: Determined indent: '{' ' * indent}'")
                return ' ' * indent
        
        print("DEBUG: Could not determine indent, returning empty string")
        return ""

    def _add_missing_component_placeholders(self, docstring: str, node: ast.AST) -> str:
        """
        Add placeholders for missing components in the docstring.

        Args:
            docstring (str): The formatted docstring.
            node (ast.AST): The AST node containing the docstring.

        Returns:
            str: The docstring with added placeholders for missing components.
        """
        print("DEBUG: Adding missing component placeholders")
        components = self._analyze_ast(node)
        lines = docstring.split("\n")
        
        new_lines = []
        for line in lines:
            new_lines.append(line)
            if any(section["marker"] in line for section in self.sections if section["marker"]):
                new_lines.append("")  # Add a blank line after each section marker
        
        for component in components:
            if component.lower() not in docstring.lower():
                if component == "Args":
                    new_lines.append("")
                    new_lines.append("Args:")
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        for arg in node.args.args:
                            if arg.arg != 'self':
                                new_lines.append(f"    {arg.arg}: NEEDS_DOCUMENTED")
                    new_lines.append("")  # Add a blank line after Args section
                elif component == "Returns" and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    new_lines.append("")
                    new_lines.append("Returns:")
                    new_lines.append("    NEEDS_DOCUMENTED")
                    new_lines.append("")  # Add a blank line after Returns section
                elif component == "Raises":
                    new_lines.append("")
                    new_lines.append("Raises:")
                    new_lines.append("    NEEDS_DOCUMENTED: NEEDS_DOCUMENTED")
                    new_lines.append("")  # Add a blank line after Raises section
                elif component == "Attributes" and isinstance(node, ast.ClassDef):
                    new_lines.append("")
                    new_lines.append("Attributes:")
                    for stmt in node.body:
                        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                            new_lines.append(f"    {stmt.target.id}: NEEDS_DOCUMENTED")
                    new_lines.append("")  # Add a blank line after Attributes section
        
        # Remove the last blank line if it exists
        if new_lines and not new_lines[-1].strip():
            new_lines.pop()
        
        result = "\n".join(new_lines)
        print(f"DEBUG: Docstring with added placeholders:\n{result}")
        return result

    def _analyze_ast(self, node: ast.AST) -> List[str]:
        """
        Analyze the AST node to identify components that should be documented.

        Args:
            node (ast.AST): The AST node to analyze.

        Returns:
            List[str]: List of components that should be documented.
        """
        print("DEBUG: Analyzing AST")
        components = []
        
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.args.args:
                components.append("Args")
            
            # Check if the function has a return statement
            has_return = any(isinstance(stmt, ast.Return) and stmt.value is not None for stmt in ast.walk(node))
            if has_return:
                components.append("Returns")
            
            for stmt in node.body:
                if isinstance(stmt, ast.Raise):
                    components.append("Raises")
                    break
        
        elif isinstance(node, ast.ClassDef):
            has_attributes = any(isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name) for stmt in node.body)
            if has_attributes:
                components.append("Attributes")
        
        print(f"DEBUG: Identified components: {components}")
        return components
