"""
tests/test_formatter.py

This module contains unit tests for the BlackPlus formatter functionality.
"""

import pytest
import os
import tempfile
from blackplus.formatter import DocstringFormatter, read_config, format_file, format_files

def test_read_config():
    """Test the read_config function with a sample configuration."""
    config = read_config("pyproject.toml")
    assert "docstrings" in config
    assert "sections" in config["docstrings"]

def test_docstring_formatter():
    """Test the DocstringFormatter class with a sample docstring."""
    config = {
        "docstrings": {
            "sections": [
                {"name": "Summary", "marker": "Summary:", "width": 72},
                {"name": "Parameters", "marker": "Parameters:", "width": 72},
                {"name": "Returns", "marker": "Returns:", "width": 72},
                {"name": "Examples", "marker": "Examples:", "width": 72, "code_example": {"start_marker": "```python", "end_marker": "```"}},
            ]
        }
    }
    formatter = DocstringFormatter(config)
    
    sample_docstring = '''
    Summary:
    This is a sample docstring.

    Parameters:
    param1 (int): An integer parameter
    param2 (str): A string parameter

    Returns:
    bool: A boolean value

    Examples:
    ```python
    result = sample_function(1, "test")
    print(result)
    ```
    '''

    formatted_docstring = formatter.format_docstring(sample_docstring)
    
    assert "This is a sample docstring." in formatted_docstring
    assert "Parameters:" in formatted_docstring
    assert "Returns:" in formatted_docstring
    assert "Examples:" in formatted_docstring
    assert "```python" in formatted_docstring
    assert "```" in formatted_docstring

def test_format_file():
    """Test the format_file function with a sample Python file."""
    config = read_config("pyproject.toml")
    
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".py", delete=False) as temp_file:
        temp_file.write('''
def sample_function(param1: int, param2: str) -> bool:
    """
    Summary:
    This is a sample function.

    Parameters:
    param1 (int): An integer parameter
    param2 (str): A string parameter

    Returns:
    bool: A boolean value

    Examples:
    ```python
    result = sample_function(1, "test")
    print(result)
    ```
    """
    return True

if __name__ == "__main__":
    print(sample_function(1, "test"))
        ''')
        temp_file.flush()
        
        format_file(temp_file.name, config)
        
        with open(temp_file.name, "r") as formatted_file:
            formatted_content = formatted_file.read()
        
        assert "def sample_function(param1: int, param2: str) -> bool:" in formatted_content
        assert '"""' in formatted_content
        assert "Summary:" in formatted_content
        assert "Parameters:" in formatted_content
        assert "Returns:" in formatted_content
        assert "Examples:" in formatted_content
        assert "```python" in formatted_content
        
    os.unlink(temp_file.name)

def test_format_files():
    """Test the format_files function with multiple sample Python files."""
    config = read_config("pyproject.toml")
    
    temp_files = []
    for i in range(3):
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".py", delete=False) as temp_file:
            temp_file.write(f'''
def function_{i}(param: int) -> str:
    """
    Summary:
    This is function {i}.

    Parameters:
    param (int): An integer parameter

    Returns:
    str: A string value
    """
    return f"Result: {{param}}"

if __name__ == "__main__":
    print(function_{i}({i}))
            ''')
            temp_file.flush()
            temp_files.append(temp_file.name)
    
    format_files(temp_files, config)
    
    for file_path in temp_files:
        with open(file_path, "r") as formatted_file:
            formatted_content = formatted_file.read()
        
        assert f"def function_{temp_files.index(file_path)}(param: int) -> str:" in formatted_content
        assert '"""' in formatted_content
        assert "Summary:" in formatted_content
        assert "Parameters:" in formatted_content
        assert "Returns:" in formatted_content
        
        os.unlink(file_path)

def test_docstring_formatter_edge_cases():
    """Test the DocstringFormatter class with edge cases."""
    config = {
        "docstrings": {
            "sections": [
                {"name": "Summary", "marker": "Summary:", "width": 72},
                {"name": "Parameters", "marker": "Parameters:", "width": 72},
                {"name": "Returns", "marker": "Returns:", "width": 72},
                {"name": "Examples", "marker": "Examples:", "width": 72, "code_example": {"start_marker": "```python", "end_marker": "```"}},
            ]
        }
    }
    formatter = DocstringFormatter(config)
    
    # Test empty docstring
    assert formatter.format_docstring("") == ""
    
    # Test docstring with only whitespace
    assert formatter.format_docstring("    \n    \n") == ""
    
    # Test docstring with no sections
    no_sections_docstring = "This is a docstring with no sections."
    assert formatter.format_docstring(no_sections_docstring).strip() == no_sections_docstring
    
    # Test docstring with invalid code example
    invalid_code_example = '''
    Examples:
    ```python
    invalid python code
    ```
    '''
    formatted = formatter.format_docstring(invalid_code_example)
    assert "Examples:" in formatted
    assert "```python" in formatted
    assert "invalid python code" in formatted
    assert "```" in formatted

# Add more tests as needed for other functions and edge cases