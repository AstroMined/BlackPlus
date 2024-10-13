import sys
import os
import shutil

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from blackplus.formatter import format_file, read_config

def main():
    config = read_config()
    
    # Create a copy of the unformatted file
    original_file = 'examples/example_unformatted_before.py'
    test_file = 'examples/example_unformatted_after.py'
    shutil.copy2(original_file, test_file)
    
    # Format the copy
    format_file(test_file, config)
    
    print(f"Formatted file: {test_file}")
    print("Please check the formatted file to verify the changes.")

if __name__ == "__main__":
    main()
