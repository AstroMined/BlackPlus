import ast
from blackplus.formatter import DocstringFormatter, DocstringTransformer, read_config

def test_google_style_docstring():
    config = {
        "docstrings": {
            "style": "google",
            "sections": [
                {"name": "Summary", "marker": "", "width": 72},
                {"name": "Args", "marker": "Args:", "width": 72},
                {"name": "Returns", "marker": "Returns:", "width": 72},
            ]
        }
    }
    
    source_lines = [
        "def test_function(param1, param2):",
        "    \"\"\"This is a test function.",
        "",
        "    Args:",
        "        param1: The first parameter.",
        "        param2: The second parameter.",
        "",
        "    Returns:",
        "        bool: True if successful, False otherwise.",
        "    \"\"\"",
        "    return True",
    ]
    
    formatter = DocstringFormatter(config, source_lines)
    transformer = DocstringTransformer(formatter)
    
    test_function = "\n".join(source_lines)
    
    print("Original function:")
    print(test_function)
    
    tree = ast.parse(test_function)
    modified_tree = transformer.visit(tree)
    formatted_function = ast.unparse(modified_tree)
    
    print("Formatted function:")
    print(formatted_function)
    
    expected_function = '''def test_function(param1, param2):
    \"\"\"This is a test function.

    Args:
        param1: The first parameter.
        param2: The second parameter.

    Returns:
        bool: True if successful, False otherwise.
    \"\"\"
    return True'''
    
    print("Expected function:")
    print(expected_function)
    
    assert formatted_function.strip() == expected_function.strip()


def test_docstring_formatter_with_code_examples():
    """Test the DocstringFormatter class with code examples in docstrings."""
    config = {
        "docstrings": {
            "sections": [
                {"name": "Summary", "marker": "", "width": 72},
                {"name": "Example", "marker": "Example:", "width": 72, "code_example": {"start_marker": "```python", "end_marker": "```"}},
            ]
        }
    }
    source_lines = [
        "def test_function(param):",
        '    """This is a test function.',
        "",
        "    Example:",
        "    ```python",
        "    result = test_function(42)",
        "    print(result)",
        "    ```",
        '    """',
        "    pass",
    ]
    formatter = DocstringFormatter(config, source_lines)
    
    sample_docstring = '''
    This function calculates the area.

    Example:
    ```python
    area = calculate_area(5)
    print("Area:", area)
    ```
    '''

    formatted_docstring = formatter.format_docstring(sample_docstring, ast.FunctionDef())
    assert "```python" in formatted_docstring
    assert "```" in formatted_docstring

def test_docstring_formatter_identify_section():
    """Test the _identify_section method of DocstringFormatter."""
    config = {
        "docstrings": {
            "sections": [
                {"name": "Summary", "marker": "", "width": 72},
                {"name": "Parameters", "marker": "Parameters:", "width": 72},
            ]
        }
    }
    source_lines = ["def test_function():"]
    formatter = DocstringFormatter(config, source_lines)

    section, content = formatter._identify_section("", ast.FunctionDef())
    assert section["name"] == "Summary"
    
    section, content = formatter._identify_section("Parameters:", ast.FunctionDef())
    assert section["name"] == "Parameters"

def test_edge_cases():
    """Test various edge cases in formatting."""
    config = read_config("pyproject.toml")
    source_lines = ["# Empty file"]
    formatter = DocstringFormatter(config, source_lines)
    
    # Test empty docstring
    empty_docstring = formatter.format_docstring("", ast.FunctionDef())
    assert empty_docstring.strip() == '""""""'

    # Test docstring with only whitespace
    whitespace_docstring = formatter.format_docstring("   \n   ", ast.FunctionDef())
    assert whitespace_docstring.strip() == '""""""'

    # Test docstring with no sections
    no_sections_docstring = formatter.format_docstring("This is a docstring without sections.", ast.FunctionDef())
    assert "This is a docstring without sections." in no_sections_docstring

# Add more test cases as needed