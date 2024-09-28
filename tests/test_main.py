"""
tests/test_main.py

This module contains unit tests for the BlackPlus __main__.py functionality.
"""

import pytest
from unittest.mock import patch
import runpy

def test_main_execution():
    """Test that the main function is called when __main__.py is executed."""
    with patch('blackplus.cli.main') as mock_main:
        runpy.run_module('blackplus.__main__', run_name='__main__')
        mock_main.assert_called_once()

if __name__ == "__main__":
    pytest.main()