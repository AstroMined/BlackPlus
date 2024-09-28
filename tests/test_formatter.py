"""
tests/test_formatter.py

This module contains unit tests for the BlackPlus formatter functionality.
"""

import pytest
import os
import tempfile
import ast
from unittest.mock import patch, MagicMock
from blackplus.formatter import DocstringFormatter, read_config, format_file, format_files, run_black, run_isort, DocstringTransformer

def test_read_config():
    """Test the read_config function with a sample configuration."""
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".toml", delete=False) as temp_file:
        temp_file.write('''
[tool.blackplus.docstrings]
sections = [
    {name = "Summary", marker = "", width = 72},
    {name = "Parameters", marker = "Parameters:", width = 72},
    {name = "Returns", marker = "Returns:", width = 72},
    {name = "Example", marker = "Example:", width = 72, code_example = {start_marker = "```python", end_marker = "```"}},
]
''')
        temp_file.flush()
        config = read_config(temp_file.name)
        assert "docstrings" in config
        assert "sections" in config["docstrings"]
        assert len(config["docstrings"]["sections"]) == 4
    os.unlink(temp_file.name)

def test_docstring_formatter_basic():
    """Test the DocstringFormatter class with a basic docstring."""
    config = {
        "docstrings": {
            "sections": [
                {"name": "Summary", "marker": "", "width": 72},
                {"name": "Parameters", "marker": "Parameters:", "width": 72},
                {"name": "Returns", "marker": "Returns:", "width": 72},
                {"name": "Example", "marker": "Example:", "width": 72, "code_example": {"start_marker": "```python", "end_marker": "```"}},
            ]
        }
    }
    formatter = DocstringFormatter(config)
    
    sample_docstring = '''
    This function does something.

    Parameters:
    param1 (int): An integer parameter.
    param2 (str): A string parameter.

    Returns:
    bool: A boolean value.
    '''
    
    formatted_docstring = formatter.format_docstring(sample_docstring)
    
    assert "This function does something." in formatted_docstring
    assert "Parameters:" in formatted_docstring
    assert "Returns:" in formatted_docstring

def test_docstring_formatter_with_code_examples():
    """Test the DocstringFormatter class with code examples in docstrings."""
    config = {
        "docstrings": {
            "sections": [
                {"name": "Summary", "marker": "", "width": 72},
                {"name": "Parameters", "marker": "Parameters:", "width": 72},
                {"name": "Returns", "marker": "Returns:", "width": 72},
                {"name": "Example", "marker": "Example:", "width": 72, "code_example": {"start_marker": "```python", "end_marker": "```"}},
            ]
        }
    }
    formatter = DocstringFormatter(config)
    
    sample_docstring = '''
    This function calculates the area.

    Example:
    ```python
    area = calculate_area(5)
    print("Area:", area)
    ```
    '''
    
    formatted_docstring = formatter.format_docstring(sample_docstring)
    
    assert "Example:" in formatted_docstring
    assert "```python" in formatted_docstring
    assert "area = calculate_area(5)" in formatted_docstring
    assert "print(\"Area:\", area)" in formatted_docstring
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
    formatter = DocstringFormatter(config)

    assert formatter._identify_section("") == {"name": "Summary", "marker": "", "width": 72}
    assert formatter._identify_section("Parameters:") == {"name": "Parameters", "marker": "Parameters:", "width": 72}
    assert formatter._identify_section("Unknown:") is None

def test_docstring_formatter_format_section():
    """Test the _format_section method of DocstringFormatter."""
    config = {
        "docstrings": {
            "sections": [
                {"name": "Summary", "marker": "", "width": 72},
                {"name": "Parameters", "marker": "Parameters:", "width": 72},
            ]
        }
    }
    formatter = DocstringFormatter(config)

    section = {"name": "Summary", "marker": "", "width": 10}
    content = ["This is a long summary that should be wrapped."]
    formatted = formatter._format_section(section, content)
    assert "This is a\nlong\nsummary\nthat\nshould be\nwrapped." in formatted

    section = {"name": "Parameters", "marker": "Parameters:", "width": 72}
    content = ["param1 (int): An integer parameter.", "param2 (str): A string parameter."]
    formatted = formatter._format_section(section, content)
    assert formatted.startswith("Parameters:")
    assert "param1 (int): An integer parameter." in formatted
    assert "param2 (str): A string parameter." in formatted

@patch('blackplus.formatter.black.format_file_in_place')
def test_run_black(mock_format_file_in_place):
    """Test the run_black function."""
    config = {"black": {"line_length": 100, "target_version": ["py38"]}}
    run_black("test_file.py", config)
    mock_format_file_in_place.assert_called_once()

@patch('blackplus.formatter.isort.file')
def test_run_isort(mock_isort_file):
    """Test the run_isort function."""
    config = {"isort": {"profile": "black"}}
    run_isort("test_file.py", config)
    mock_isort_file.assert_called_once_with("test_file.py", profile="black")

def test_docstring_transformer():
    """Test the DocstringTransformer class."""
    config = {
        "docstrings": {
            "sections": [
                {"name": "Summary", "marker": "", "width": 72},
            ]
        }
    }
    formatter = DocstringFormatter(config)
    transformer = DocstringTransformer(formatter)

    # Test function docstring transformation
    func_node = ast.parse('''
def test_func():
    """This is a test function."""
    pass
''')
    transformed_func = transformer.visit(func_node.body[0])
    assert ast.get_docstring(transformed_func) == "This is a test function."

    # Test class docstring transformation
    class_node = ast.parse('''
class TestClass:
    """This is a test class."""
    pass
''')
    transformed_class = transformer.visit(class_node.body[0])
    assert ast.get_docstring(transformed_class) == "This is a test class."

@patch('blackplus.formatter.run_black')
@patch('blackplus.formatter.run_isort')
def test_format_file(mock_run_isort, mock_run_black):
    """Test the format_file function."""
    config = {
        "docstrings": {
            "sections": [
                {"name": "Summary", "marker": "", "width": 72},
            ]
        }
    }
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".py", delete=False) as temp_file:
        temp_file.write('''
def test_func():
    """This is a test function."""
    pass
''')
        temp_file.flush()
        format_file(temp_file.name, config)
        mock_run_black.assert_called_once_with(temp_file.name, config)
        mock_run_isort.assert_called_once_with(temp_file.name, config)
    os.unlink(temp_file.name)

def test_format_file_functions():
    """Test formatting of functions in a Python file."""
    config = read_config("pyproject.toml")
    
    unformatted_code = '''
def  calculate_area(radius):
  """This function calculates the area of a circle given its radius.
  The formula used is: area = pi * radius^2
  Parameters:
  radius (float): The radius of the circle for which the area will be calculated
  Returns:
  float: The area of the circle.
  Example:
      ```python
        area = calculate_area( 5 )
        print( "Area:",area )
      ```
  """
  pi = 3.141592653589793
  area=pi*radius*radius
  return area
'''
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".py", delete=False) as temp_file:
        temp_file.write(unformatted_code)
        temp_file.flush()
        
        format_file(temp_file.name, config)
        
        with open(temp_file.name, "r") as formatted_file:
            formatted_content = formatted_file.read()
        
        # Check for correct function definition formatting
        assert "def calculate_area(radius):" in formatted_content
        # Check for formatted docstring
        assert '"""' in formatted_content
        assert "This function calculates the area of a circle given its radius." in formatted_content
        assert "Parameters:" in formatted_content
        assert "Returns:" in formatted_content
        assert "Example:" in formatted_content
        # Check code example formatting (content should remain unchanged)
        assert "```python" in formatted_content
        assert "area = calculate_area( 5 )" in formatted_content
        assert "print( \"Area:\",area )" in formatted_content
        assert "```" in formatted_content
    
    os.unlink(temp_file.name)

def test_format_file_classes():
    """Test formatting of classes and methods in a Python file."""
    config = read_config("pyproject.toml")
    
    unformatted_code = '''
class  MyClass:
    """This is a sample class with methods that do simple operations.
    It demonstrates poor formatting in docstrings and code.
    Attributes:
    value (int): An integer value associated with the class.
    Example:
        ```python
            obj = MyClass( 42 )
            obj.increment_value( )
            print( obj.value )
        ```
    """
    def __init__(self,value):
        self.value=value

    def increment_value(self):
      """Increments the value by one."""
      self.value=self.value+1

    def multiply_value(self,factor):
          """Multiplies the value by the given factor and returns the result."""
          return self.value*factor
'''
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".py", delete=False) as temp_file:
        temp_file.write(unformatted_code)
        temp_file.flush()
        
        format_file(temp_file.name, config)
        
        with open(temp_file.name, "r") as formatted_file:
            formatted_content = formatted_file.read()
        
        # Check for correct class definition formatting
        assert "class MyClass:" in formatted_content
        # Check for formatted docstring (content should remain unchanged)
        assert '"""' in formatted_content
        assert "This is a sample class with methods that do simple operations." in formatted_content
        assert "Attributes:" in formatted_content
        assert "Example:" in formatted_content
        # Check method formatting
        assert "def __init__(self, value):" in formatted_content
        assert "def increment_value(self):" in formatted_content
        assert "def multiply_value(self, factor):" in formatted_content
        # Check code example formatting (content should remain unchanged)
        assert "```python" in formatted_content
        assert "obj = MyClass( 42 )" in formatted_content
        assert "obj.increment_value( )" in formatted_content
        assert "print( obj.value )" in formatted_content
        assert "```" in formatted_content
    
    os.unlink(temp_file.name)

def test_format_file_full_script():
    """Test formatting of the entire unformatted example script."""
    config = read_config("pyproject.toml")
    
    # Replace this string with the unformatted example code (without triple backticks)
    unformatted_code = '''
def  calculate_area(radius):
  """This function calculates the area of a circle given its radius.
  The formula used is: area = pi * radius^2
  Parameters:
  radius (float): The radius of the circle for which the area will be calculated
  Returns:
  float: The area of the circle.
  Example:
      ```python
        area = calculate_area( 5 )
        print( "Area:",area )
      ```
  """
  pi = 3.141592653589793
  area=pi*radius*radius
  return area

def   complex_function(x,   y):
      """Performs a complex calculation on two numbers and returns the result which includes addition, subtraction, multiplication, and division.
      Parameters:
          x (int): The first number.
          y (int): The second number.
      Returns:
          dict: A dictionary containing the results of various operations.
      Example:
          # Example usage of complex_function
          result = complex_function(10,5)
          print("Results:",result)
      """
      results={}
      results[ 'add' ]=x + y
      results[ 'subtract']=x - y
      results['multiply' ]=x*y
      results['divide']=x / y
      return results

class  MyClass:
    """This is a sample class with methods that do simple operations.
    It demonstrates poor formatting in docstrings and code.
    Attributes:
    value (int): An integer value associated with the class.
    Example:
        ```python
            obj = MyClass( 42 )
            obj.increment_value( )
            print( obj.value )
        ```
    """
    def __init__(self,value):
        self.value=value

    def increment_value(self):
      """Increments the value by one."""
      self.value=self.value+1

    def multiply_value(self,factor):
          """Multiplies the value by the given factor and returns the result."""
          return self.value*factor
'''
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".py", delete=False) as temp_file:
        temp_file.write(unformatted_code)
        temp_file.flush()
        
        format_file(temp_file.name, config)
        
        with open(temp_file.name, "r") as formatted_file:
            formatted_content = formatted_file.read()
        
        # Check that all functions and classes are correctly formatted
        assert "def calculate_area(radius):" in formatted_content
        assert "def complex_function(x, y):" in formatted_content
        assert "class MyClass:" in formatted_content
        # Additional checks can be added here for docstrings and code examples
    
    os.unlink(temp_file.name)

def test_format_files_multiple():
    """Test the format_files function with multiple sample Python files."""
    config = read_config("pyproject.toml")
    
    temp_files = []
    for i in range(3):
        unformatted_code = f'''
def   function_{i}(param):
  """This function does something with param {i}.
  Parameters:
  param (int): An integer parameter.
  Returns:
  str: A string value.
  """
  return f"Result {{param}}"
'''
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".py", delete=False) as temp_file:
            temp_file.write(unformatted_code)
            temp_file.flush()
            temp_files.append(temp_file.name)
    
    format_files(temp_files, config)
    
    for file_path in temp_files:
        with open(file_path, "r") as formatted_file:
            formatted_content = formatted_file.read()
        
        # Check for correct function definition formatting
        function_name = f"function_{temp_files.index(file_path)}"
        assert f"def {function_name}(param):" in formatted_content
        # Check for formatted docstring
        assert '"""' in formatted_content
        assert f"This function does something with param {temp_files.index(file_path)}." in formatted_content
        assert "Parameters:" in formatted_content
        assert "Returns:" in formatted_content
        
        os.unlink(file_path)

def test_edge_cases():
    """Test various edge cases in formatting."""
    config = read_config("pyproject.toml")
    formatter = DocstringFormatter(config)
    
    # Edge case: Missing docstring
    sample_code_no_docstring = '''
def function_without_docstring(param):
    pass
'''
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".py", delete=False) as temp_file:
        temp_file.write(sample_code_no_docstring)
        temp_file.flush()
        
        format_file(temp_file.name, config)
        
        with open(temp_file.name, "r") as formatted_file:
            formatted_content = formatted_file.read()
        
        # Ensure the function is still present and correctly formatted
        assert "def function_without_docstring(param):" in formatted_content
        # Since there was no docstring, nothing should be added
        assert formatted_content.count('"""') == 0
    
    os.unlink(temp_file.name)
    
    # Edge case: Invalid code example in docstring
    invalid_code_example = '''
def function_with_invalid_example():
    """Function with invalid code example.

    Example:
    ```python
    def incomplete_code(
    ```
    """
    pass
'''
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".py", delete=False) as temp_file:
        temp_file.write(invalid_code_example)
        temp_file.flush()
        
        format_file(temp_file.name, config)
        
        with open(temp_file.name, "r") as formatted_file:
            formatted_content = formatted_file.read()
        
        # Ensure that the docstring is still present
        assert '"""' in formatted_content
        assert "Function with invalid code example." in formatted_content
        # Check that the invalid code example is handled gracefully
        assert "Example:" in formatted_content
        assert "```python" in formatted_content
        assert "def incomplete_code(" in formatted_content
        assert "```" in formatted_content
    
    os.unlink(temp_file.name)

def test_formatting_preserves_code_behavior():
    """Ensure that formatting does not change code behavior."""
    config = read_config("pyproject.toml")
    
    unformatted_code = '''
def add_numbers(a,b):
  """Adds two numbers together."""
  return a+  b
'''
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".py", delete=False) as temp_file:
        temp_file.write(unformatted_code)
        temp_file.flush()
        
        # Save original output
        original_result = {}
        exec(unformatted_code, original_result)
        original_output = original_result['add_numbers'](2, 3)
        
        format_file(temp_file.name, config)
        
        with open(temp_file.name, "r") as formatted_file:
            formatted_content = formatted_file.read()
        
        # Execute formatted code
        formatted_result = {}
        exec(formatted_content, formatted_result)
        formatted_output = formatted_result['add_numbers'](2, 3)
        
        # Check that outputs are the same
        assert original_output == formatted_output
    
    os.unlink(temp_file.name)

def test_handling_of_syntax_errors():
    """Test how the formatter handles files with syntax errors."""
    config = read_config("pyproject.toml")
    
    code_with_syntax_error = '''
def broken_function():
    print("This function has a syntax error"
'''
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".py", delete=False) as temp_file:
        temp_file.write(code_with_syntax_error)
        temp_file.flush()
        
        # Attempt to format the file
        try:
            format_file(temp_file.name, config)
            assert False, "Expected an exception due to syntax error, but none occurred."
        except SyntaxError:
            pass  # Expected outcome
        except Exception as e:
            assert False, f"Unexpected exception type: {e}"
        finally:
            os.unlink(temp_file.name)

def test_format_file_nonexistent_path():
    """Test formatting with a nonexistent file path."""
    config = read_config("pyproject.toml")
    nonexistent_path = "/path/to/nonexistent/file.py"
    
    with pytest.raises(FileNotFoundError):
        format_file(nonexistent_path, config)

def test_format_files_empty_list():
    """Test formatting with an empty list of files."""
    config = read_config("pyproject.toml")
    format_files([], config)  # Should not raise an exception

@patch('blackplus.formatter.format_file')
def test_format_files(mock_format_file):
    """Test the format_files function."""
    config = {}
    file_paths = ["file1.py", "file2.py"]
    format_files(file_paths, config)
    assert mock_format_file.call_count == 2
    mock_format_file.assert_any_call("file1.py", config)
    mock_format_file.assert_any_call("file2.py", config)

if __name__ == "__main__":
    pytest.main()
