# BlackPlus

BlackPlus is a Python package that extends the functionality of Black to format both code and docstrings with custom configurations. It combines the power of Black for code formatting, isort for import sorting, and custom docstring formatting based on user-defined configurations.

## Features

- Runs Black for code formatting using configurations from `pyproject.toml`
- Runs isort to sort imports
- Formats docstrings based on user-defined configurations
- Identifies and formats code examples within docstrings using Black
- Provides a command-line interface for easy use

## Installation

You can install BlackPlus using pip:

```bash
pip install blackplus
```

## Usage

### Command Line Interface

BlackPlus can be used from the command line to format Python files or directories:

```bash
blackplus path/to/file_or_directory
```

You can specify multiple files or directories:

```bash
blackplus file1.py file2.py path/to/directory
```

### Configuration

BlackPlus uses `pyproject.toml` for configuration. Here's an example configuration:

```toml
[tool.black]
line-length = 88
target-version = ['py38']

[tool.isort]
profile = "black"

[tool.blackplus]
[tool.blackplus.docstrings]
sections = [
    {name = "Summary", marker = "", width = 72},
    {name = "Parameters", marker = "Parameters:", width = 72},
    {name = "Returns", marker = "Returns:", width = 72},
    {name = "Examples", marker = "Examples:", width = 72, code_example = {start_marker = "```python", end_marker = "```"}},
]
```

### Python API

You can also use BlackPlus programmatically in your Python code:

```python
from blackplus import format_file, format_files, read_config

# Format a single file
config = read_config("pyproject.toml")
format_file("path/to/file.py", config)

# Format multiple files
python_files = ["file1.py", "file2.py", "file3.py"]
format_files(python_files, config)
```

## Development

To set up the development environment:

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/BlackPlus.git
   cd BlackPlus
   ```

2. Install dependencies using Poetry:
   ```bash
   poetry install
   ```

3. Activate the virtual environment:
   ```bash
   poetry shell
   ```

4. Run tests:
   ```bash
   pytest
   ```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
