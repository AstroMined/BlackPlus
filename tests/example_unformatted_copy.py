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
          ```python
          # Example usage of complex_function
          result = complex_function(10,5)
          print("Results:",result)
          ```
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
