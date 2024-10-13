"""This is a poorly formatted module docstring. It should be reformatted to follow the Google Style Guide."""

def function_with_pep484_type_annotations(param1: int, param2: str) -> bool:
    """Example function with PEP 484 type annotations.
    Args:
    param1: The first parameter.
    param2: The second parameter.
    Returns:
    The return value. True for success, False otherwise."""
    return param1 == len(param2)

def function_with_long_parameter_descriptions(param1: str, param2: str, param3: str):
    """Example function with long parameter descriptions.
    Args:
        param1: This is a very long description for the first parameter that should be wrapped to the next line.
        param2: This is another long description for the second parameter that should also be wrapped.
        param3: Yet another long description for the third parameter to demonstrate wrapping behavior.
    Returns:
        A concatenated string of all parameters."""
    return param1 + param2 + param3

def function_with_exceptions():
    """Example function that raises an exception.
    Raises:
    ValueError: If something goes wrong."""
    raise ValueError("Something went wrong")

class ExampleClass:
    """Example class with various methods and attributes.
    This class demonstrates different types of methods and how their
    docstrings should be formatted.
    Attributes:
    attr1: Description of attr1.
    attr2: Description of attr2."""

    def __init__(self, attr1: int, attr2: str):
        """Initialize ExampleClass.
        Args:
        attr1: Description of attr1.
        attr2: Description of attr2."""
        self.attr1 = attr1
        self.attr2 = attr2

    def method_with_no_arguments(self):
        """Perform an operation without arguments."""
        pass

    def method_with_args_kwargs(self, arg1, *args, **kwargs):
        """Perform an operation with a combination of arguments.
        Args:
        arg1: Description of arg1.
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments."""
        pass

    @property
    def some_property(self):
        """Get the value of some_property."""
        return self.attr1 + len(self.attr2)

def function_with_yield():
    """Example of a generator function.
    Yields:
    The next number in the sequence."""
    yield 1
    yield 2
    yield 3

# Function without any docstring
def function_without_docstring(param1, param2):
    return param1 + param2

# New examples with poorly formatted docstrings

def function_with_poorly_formatted_args_returns(param1: int, param2: str) -> dict:
    """
    This function has poorly formatted Args and Returns sections.
    Args:
    param1 - An integer parameter
    param2 - A string parameter
    Returns:
    A dictionary containing the parameters"""
    return {"param1": param1, "param2": param2}

class PoorlyFormattedClass:
    """A class with a poorly formatted Attributes section.
    Attributes:
    attr1 - An integer attribute
    attr2 - A string attribute
    attr3 - A list attribute"""

    def __init__(self, attr1: int, attr2: str, attr3: list):
        self.attr1 = attr1
        self.attr2 = attr2
        self.attr3 = attr3

    def poorly_formatted_method(self, arg1: int, arg2: str) -> bool:
        """A method with poorly formatted Args, Returns, and Raises sections.
        Args:
        arg1: An integer argument
        arg2: A string argument
        Returns:
        A boolean value
        Raises:
        ValueError: If arg1 is negative"""
        if arg1 < 0:
            raise ValueError("arg1 must be non-negative")
        return len(arg2) == arg1

def function_with_poorly_formatted_examples(x: int, y: int) -> int:
    """A function with a poorly formatted Examples section.
    Args:
        x: The first integer
        y: The second integer
    Returns:
        The sum of x and y
    Examples:
    >>> function_with_poorly_formatted_examples(1, 2)
    3
    >>> function_with_poorly_formatted_examples(-1, 1)
    0"""
    return x + y

def function_with_poorly_formatted_notes(data: list) -> float:
    """Calculate the average of a list of numbers.
    Args:
        data: A list of numbers
    Returns:
        The average of the numbers
    Notes:
    - This function assumes the input list is not empty.
    - It uses the sum() function to calculate the total."""
    return sum(data) / len(data)

# TODO: Add more examples to cover all aspects of the Google Style Guide
