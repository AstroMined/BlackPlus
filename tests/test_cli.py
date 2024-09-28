"""
tests/test_cli.py

This module contains unit tests for the BlackPlus CLI functionality.
"""

import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from blackplus.cli import parse_arguments, get_python_files, main

def test_parse_arguments():
    """Test the argument parsing functionality."""
    with patch('sys.argv', ['blackplus', 'file1.py', 'file2.py', '--config', 'custom_config.toml']):
        args = parse_arguments()
        assert args.paths == ['file1.py', 'file2.py']
        assert args.config == 'custom_config.toml'

    with patch('sys.argv', ['blackplus', 'directory/']):
        args = parse_arguments()
        assert args.paths == ['directory/']
        assert args.config == 'pyproject.toml'

def test_get_python_files():
    """Test the function for finding Python files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create some test files
        open(os.path.join(tmpdir, 'file1.py'), 'w').close()
        open(os.path.join(tmpdir, 'file2.txt'), 'w').close()
        os.mkdir(os.path.join(tmpdir, 'subdir'))
        open(os.path.join(tmpdir, 'subdir', 'file3.py'), 'w').close()

        # Test with a single file
        assert get_python_files([os.path.join(tmpdir, 'file1.py')]) == [os.path.join(tmpdir, 'file1.py')]

        # Test with a directory
        python_files = get_python_files([tmpdir])
        assert len(python_files) == 2
        assert os.path.join(tmpdir, 'file1.py') in python_files
        assert os.path.join(tmpdir, 'subdir', 'file3.py') in python_files

        # Test with mixed input
        mixed_input = [os.path.join(tmpdir, 'file1.py'), os.path.join(tmpdir, 'subdir')]
        python_files = get_python_files(mixed_input)
        assert len(python_files) == 2
        assert os.path.join(tmpdir, 'file1.py') in python_files
        assert os.path.join(tmpdir, 'subdir', 'file3.py') in python_files

@patch('blackplus.cli.read_config')
@patch('blackplus.cli.format_files')
@patch('blackplus.cli.get_python_files')
def test_main_success(mock_get_python_files, mock_format_files, mock_read_config):
    """Test the main function with successful execution."""
    mock_get_python_files.return_value = ['file1.py', 'file2.py']
    mock_read_config.return_value = {'some': 'config'}

    with patch('sys.argv', ['blackplus', 'file1.py', 'file2.py']):
        main()

    mock_read_config.assert_called_once_with('pyproject.toml')
    mock_get_python_files.assert_called_once_with(['file1.py', 'file2.py'])
    mock_format_files.assert_called_once_with(['file1.py', 'file2.py'], {'some': 'config'})

@patch('blackplus.cli.read_config')
def test_main_config_not_found(mock_read_config):
    """Test the main function when the config file is not found."""
    mock_read_config.side_effect = FileNotFoundError()

    with patch('sys.argv', ['blackplus', 'file1.py']):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

@patch('blackplus.cli.read_config')
@patch('blackplus.cli.get_python_files')
def test_main_no_python_files(mock_get_python_files, mock_read_config):
    """Test the main function when no Python files are found."""
    mock_get_python_files.return_value = []
    mock_read_config.return_value = {'some': 'config'}

    with patch('sys.argv', ['blackplus', 'empty_dir/']):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

@patch('blackplus.cli.read_config')
@patch('blackplus.cli.get_python_files')
@patch('blackplus.cli.format_files')
def test_main_formatting_error(mock_format_files, mock_get_python_files, mock_read_config):
    """Test the main function when a formatting error occurs."""
    mock_get_python_files.return_value = ['file1.py']
    mock_read_config.return_value = {'some': 'config'}
    mock_format_files.side_effect = ValueError("Formatting error")

    with patch('sys.argv', ['blackplus', 'file1.py']):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

@patch('blackplus.cli.read_config')
@patch('blackplus.cli.get_python_files')
@patch('blackplus.cli.format_files')
def test_main_io_error(mock_format_files, mock_get_python_files, mock_read_config):
    """Test the main function when an I/O error occurs."""
    mock_get_python_files.return_value = ['file1.py']
    mock_read_config.return_value = {'some': 'config'}
    mock_format_files.side_effect = IOError("I/O error")

    with patch('sys.argv', ['blackplus', 'file1.py']):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

@patch('blackplus.cli.read_config')
@patch('blackplus.cli.get_python_files')
@patch('blackplus.cli.format_files')
def test_main_unexpected_error(mock_format_files, mock_get_python_files, mock_read_config):
    """Test the main function when an unexpected error occurs."""
    mock_get_python_files.return_value = ['file1.py']
    mock_read_config.return_value = {'some': 'config'}
    mock_format_files.side_effect = Exception("Unexpected error")

    with patch('sys.argv', ['blackplus', 'file1.py']):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

if __name__ == "__main__":
    pytest.main()