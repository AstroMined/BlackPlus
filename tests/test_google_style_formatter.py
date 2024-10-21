import ast
import pytest
from blackplus.google_formatter import GoogleDocstringFormatter
from blackplus.formatter import ASTInfo
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

@pytest.fixture
def formatter():
    config = {
        "docstrings": {
            "style": "google",
            "max_line_length": 80
        }
    }
    # Provide dummy source lines
    source_lines = [
        "def func():",
        "    '''",
        "    This is a simple summary docstring.",
        "    '''",
        "    pass"
    ]
    return GoogleDocstringFormatter(config, source_lines)

def test_simple_summary_docstring(formatter):
    original_docstring = '''
    This is a simple summary docstring.
    '''
    node = ast.parse("def func():\n    pass").body[0]
    node.body.insert(0, ast.Expr(ast.Str(original_docstring)))
    
    # Create a proper ASTInfo object
    ast_info = ASTInfo(params={}, attributes={}, return_type=None, raises=[])

    formatted_docstring = formatter.format_docstring(original_docstring, ast_info)
    expected_docstring = '''    """This is a simple summary docstring."""'''

    print("DEBUG: Formatted docstring:")
    print(repr(formatted_docstring))
    print("DEBUG: Expected docstring:")
    print(repr(expected_docstring))
    
    assert formatted_docstring == expected_docstring

def test_add_missing_components(formatter):
    original_docstring = '''
    This function does something.
    '''
    node = ast.parse("def func(param1, param2):\n    pass").body[0]
    node.body.insert(0, ast.Expr(ast.Str(original_docstring)))

    # Create a proper ASTInfo object
    ast_info = ASTInfo(params={"param1": "Any", "param2": "Any"}, attributes={}, return_type=None, raises=[])

    formatted_docstring = formatter.format_docstring(original_docstring, ast_info)
    expected_docstring = '''    """This function does something.

    Args:
        param1: NEEDS_DOCUMENTED
        param2: NEEDS_DOCUMENTED

    """'''
    
    print("DEBUG: Formatted docstring:")
    print(repr(formatted_docstring))
    print("DEBUG: Expected docstring:")
    print(repr(expected_docstring))
    
    assert formatted_docstring == expected_docstring

def test_format_class_docstring(formatter):
    original_docstring = '''
    A sample class.

    This class demonstrates docstring formatting.

    Attributes:
        attr1: The first attribute.
        attr2: The second attribute.
    '''
    class_def = '''
class SampleClass:
    attr1: int
    attr2: str
    '''
    node = ast.parse(class_def).body[0]
    node.body.insert(0, ast.Expr(ast.Str(original_docstring)))

    # Create a proper ASTInfo object
    ast_info = ASTInfo(params={}, attributes={"attr1": "int", "attr2": "str"}, return_type=None, raises=[])

    formatted_docstring = formatter.format_docstring(original_docstring, ast_info)
    expected_docstring = '''    """A sample class.

    This class demonstrates docstring formatting.

    Attributes:
        attr1 (int): The first attribute.
        attr2 (str): The second attribute.

    """'''

    print("DEBUG: Formatted docstring:")
    print(repr(formatted_docstring))
    print("DEBUG: Expected docstring:")
    print(repr(expected_docstring))
    
    assert formatted_docstring == expected_docstring

def test_format_function_docstring(formatter):
    original_docstring = '''
    This function does something.


    Returns:
    The result of the operation.

    Raises:
    ValueError: If something goes wrong.
    '''
    node = ast.parse("def func():\n    pass").body[0]
    node.body.insert(0, ast.Expr(ast.Str(original_docstring)))

    # Create a proper ASTInfo object
    ast_info = ASTInfo(params={}, attributes={}, return_type="Any", raises=["ValueError"])

    formatted_docstring = formatter.format_docstring(original_docstring, ast_info)
    expected_docstring = '''    """This function does something.

    Returns:
        The result of the operation.

    Raises:
        ValueError: If something goes wrong.

    """'''

    print("DEBUG: Formatted docstring:")
    print(repr(formatted_docstring))
    print("DEBUG: Expected docstring:")
    print(repr(expected_docstring))
    
    assert formatted_docstring == expected_docstring

def test_long_parameter_description(formatter):
    original_docstring = '''
    This function does something.

    Args:
        param1: This is a very long parameter description that should be wrapped to the next line.
    '''
    node = ast.parse("def func(param1):\n    pass").body[0]
    node.body.insert(0, ast.Expr(ast.Str(original_docstring)))

    # Create a proper ASTInfo object
    ast_info = ASTInfo(params={"param1": "Any"}, attributes={}, return_type=None, raises=[])

    formatted_docstring = formatter.format_docstring(original_docstring, ast_info)
    expected_docstring = '''    """This function does something.

    Args:
        param1: This is a very long parameter description that should be
            wrapped to the next line.

    """'''

    print("DEBUG: Formatted docstring:")
    print(formatted_docstring)
    print("DEBUG: Expected docstring:")
    print(expected_docstring)
    print(f"FORMATTED: {repr(formatted_docstring)}")
    print(f" EXCPETED: {repr(expected_docstring)}")

    assert formatted_docstring == expected_docstring

# New test cases for poorly formatted docstrings

def test_poorly_formatted_args_returns(formatter):
    original_docstring = '''
    This function has poorly formatted Args and Returns sections.
    Args:
    param1 - An integer parameter
    param2 - A string parameter
    Returns:
    A dictionary containing the parameters
    '''
    node = ast.parse("def func(param1: int, param2: str) -> dict:\n    pass").body[0]
    node.body.insert(0, ast.Expr(ast.Str(original_docstring)))

    # Create a proper ASTInfo object
    ast_info = ASTInfo(params={"param1": "int", "param2": "str"}, attributes={}, return_type="dict", raises=[])

    formatted_docstring = formatter.format_docstring(original_docstring, ast_info)
    expected_docstring = '''    """This function has poorly formatted Args and Returns sections.

    Args:
        param1 (int): An integer parameter
        param2 (str): A string parameter

    Returns:
        dict: A dictionary containing the parameters

    """'''

    print("DEBUG: Formatted docstring:")
    print(repr(formatted_docstring))
    print("DEBUG: Expected docstring:")
    print(repr(expected_docstring))

    assert formatted_docstring == expected_docstring

def test_poorly_formatted_class_attributes(formatter):
    original_docstring = '''A class with a poorly formatted Attributes section.
    Attributes:
    attr1 - An integer attribute
    attr2 - A string attribute
    attr3 - A list attribute'''
    class_def = '''
class PoorlyFormattedClass:
    attr1: int
    attr2: str
    attr3: list
    '''
    node = ast.parse(class_def).body[0]
    node.body.insert(0, ast.Expr(ast.Str(original_docstring)))

    # Create a proper ASTInfo object
    ast_info = ASTInfo(params={}, attributes={"attr1": "int", "attr2": "str", "attr3": "list"}, return_type=None, raises=[])

    formatted_docstring = formatter.format_docstring(original_docstring, ast_info)
    expected_docstring = '''    """A class with a poorly formatted Attributes section.

    Attributes:
        attr1 (int): An integer attribute
        attr2 (str): A string attribute
        attr3 (list): A list attribute

    """'''

    print("DEBUG: Formatted docstring:")
    print(repr(formatted_docstring))
    print("DEBUG: Expected docstring:")
    print(repr(expected_docstring))

    assert formatted_docstring == expected_docstring

def test_poorly_formatted_method(formatter):
    original_docstring = '''A method with poorly formatted Args, Returns, and Raises sections.
    Args:
    arg1: An integer argument
    arg2: A string argument
    Returns:
    A boolean value
    Raises:
    ValueError: If arg1 is negative'''
    node = ast.parse("def poorly_formatted_method(self, arg1: int, arg2: str) -> bool:\n    pass").body[0]
    node.body.insert(0, ast.Expr(ast.Str(original_docstring)))

    # Create a proper ASTInfo object
    ast_info = ASTInfo(params={"arg1": "int", "arg2": "str"}, attributes={}, return_type="bool", raises=["ValueError"])

    formatted_docstring = formatter.format_docstring(original_docstring, ast_info)
    expected_docstring = '''    """A method with poorly formatted Args, Returns, and Raises sections.

    Args:
        arg1 (int): An integer argument
        arg2 (str): A string argument

    Returns:
        bool: A boolean value

    Raises:
        ValueError: If arg1 is negative

    """'''

    print("DEBUG: Formatted docstring:")
    print(repr(formatted_docstring))
    print("DEBUG: Expected docstring:")
    print(repr(expected_docstring))

    assert formatted_docstring == expected_docstring

def test_poorly_formatted_examples(formatter):
    original_docstring = '''A function with a poorly formatted Examples section.
    Args:
        x: The first integer
        y: The second integer
    Returns:
        The sum of x and y
    Examples:
    >>> function_with_poorly_formatted_examples(1, 2)
    3
    >>> function_with_poorly_formatted_examples(-1, 1)
    0'''
    node = ast.parse("def function_with_poorly_formatted_examples(x: int, y: int) -> int:\n    pass").body[0]
    node.body.insert(0, ast.Expr(ast.Str(original_docstring)))

    # Create a proper ASTInfo object
    ast_info = ASTInfo(params={"x": "int", "y": "int"}, attributes={}, return_type="int", raises=[])

    formatted_docstring = formatter.format_docstring(original_docstring, ast_info)
    expected_docstring = '''    """A function with a poorly formatted Examples section.

    Args:
        x (int): The first integer
        y (int): The second integer

    Returns:
        int: The sum of x and y

    Examples:
        >>> function_with_poorly_formatted_examples(1, 2)
        3
        >>> function_with_poorly_formatted_examples(-1, 1)
        0

    """'''

    print("DEBUG: Formatted docstring:")
    print(repr(formatted_docstring))
    print("DEBUG: Expected docstring:")
    print(repr(expected_docstring))

    assert formatted_docstring == expected_docstring

def test_poorly_formatted_notes(formatter):
    original_docstring = '''Calculate the average of a list of numbers.
    Args:
        data: A list of numbers
    Returns:
        The average of the numbers
    Notes:
    - This function assumes the input list is not empty.
    - It uses the sum() function to calculate the total.'''
    node = ast.parse("def function_with_poorly_formatted_notes(data: list) -> float:\n    pass").body[0]
    node.body.insert(0, ast.Expr(ast.Str(original_docstring)))

    # Create a proper ASTInfo object
    ast_info = ASTInfo(params={"data": "list"}, attributes={}, return_type="float", raises=[])

    formatted_docstring = formatter.format_docstring(original_docstring, ast_info)
    expected_docstring = '''    """Calculate the average of a list of numbers.

    Args:
        data (list): A list of numbers

    Returns:
        float: The average of the numbers

    Notes:
        - This function assumes the input list is not empty.
        - It uses the sum() function to calculate the total.

    """'''

    print("DEBUG: Formatted docstring:")
    print(repr(formatted_docstring))
    print("DEBUG: Expected docstring:")
    print(repr(expected_docstring))

    assert formatted_docstring == expected_docstring

def test_multi_paragraph_description(formatter):
    original_docstring = '''This function has a multi-paragraph description.

    The first paragraph provides a brief overview of the function's purpose and the logic behind it. It explains why the function is needed and what it aims to achieve.

    The second paragraph goes into more detail about the function's behavior and usage. It explains the input parameters, the expected output, and any special considerations.

    Args:
        param1: A parameter with a multi-line description.
            This is the second paragraph of the parameter's description.

        param2: Another parameter with a single-line description.

    Returns:
        A complex object with multiple properties.
    '''
    node = ast.parse("def func_with_multi_paragraph(param1, param2):\n    pass").body[0]
    node.body.insert(0, ast.Expr(ast.Str(original_docstring)))

    # Create a proper ASTInfo object
    ast_info = ASTInfo(params={"param1": "Any", "param2": "Any"}, attributes={}, return_type="Any", raises=[])

    formatted_docstring = formatter.format_docstring(original_docstring, ast_info)
    expected_docstring = '''    """This function has a multi-paragraph description.

    The first paragraph provides a brief overview of the function's
    purpose and the logic behind it. It explains why the function is
    needed and what it aims to achieve.

    The second paragraph goes into more detail about the function's
    behavior and usage. It explains the input parameters, the expected
    output, and any special considerations.

    Args:
        param1: A parameter with a multi-line description.

            This is the second paragraph of the parameter's description.
        param2: Another parameter with a single-line description.

    Returns:
        A complex object with multiple properties.

    """'''

    print("DEBUG: Formatted docstring:")
    print(formatted_docstring)
    print("DEBUG: Expected docstring:")
    print(expected_docstring)
    print(f"FORMATTED: {repr(formatted_docstring)}")
    print(f" EXCPETED: {repr(expected_docstring)}")

    assert formatted_docstring == expected_docstring

def test_docstring_with_code_block(formatter):
    original_docstring = '''A function with a code block in its docstring.

    This function demonstrates how to use code blocks in docstrings.

    Example:
        Here's an example of how to use this function:

        ```python
        result = function_with_code_block(42)
        print(result)
        ```

    Args:
        value: An integer value to process.

    Returns:
        The processed value.
    '''
    node = ast.parse("def function_with_code_block(value: int) -> int:\n    pass").body[0]
    node.body.insert(0, ast.Expr(ast.Str(original_docstring)))

    # Create a proper ASTInfo object
    ast_info = ASTInfo(params={"value": "int"}, attributes={}, return_type="int", raises=[])

    formatted_docstring = formatter.format_docstring(original_docstring, ast_info)
    expected_docstring = '''    """A function with a code block in its docstring.

    This function demonstrates how to use code blocks in docstrings.

    Example:
        Here's an example of how to use this function:

        ```python
        result = function_with_code_block(42)
        print(result)
        ```

    Args:
        value (int): An integer value to process.

    Returns:
        int: The processed value.

    """'''

    print("DEBUG: Formatted docstring:")
    print(formatted_docstring)
    print("DEBUG: Expected docstring:")
    print(expected_docstring)
    print(f"FORMATTED: {repr(formatted_docstring)}")
    print(f" EXCPETED: {repr(expected_docstring)}")


    assert formatted_docstring == expected_docstring

if __name__ == '__main__':
    pytest.main()
