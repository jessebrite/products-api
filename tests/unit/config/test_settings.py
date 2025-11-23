import os
import builtins
import pytest
from unittest.mock import mock_open, patch
from src.config.settings import read_pyproject_metadata

# Sample valid pyproject.toml content (minimal)
valid_pyproject_toml = b"""
[project]
name = "Test API"
description = "A test API description"
"""

# Sample invalid pyproject.toml content (malformed)
invalid_pyproject_toml = b"""
[project
name = "Test API"
"""

def test_read_pyproject_metadata_valid_files():
    m_open = mock_open()
    # Mock the pyproject.toml and version.txt file reads with valid content
    m_open.side_effect = [
        mock_open(read_data=valid_pyproject_toml).return_value,
        mock_open(read_data="1.2.3\n").return_value
    ]
    with patch("builtins.open", m_open), \
         patch("os.path.exists", return_value=True):
        name, desc, version = read_pyproject_metadata()
        assert name == "Test API"
        assert desc == "A test API description"
        assert version == "1.2.3"

def test_read_pyproject_metadata_missing_version_file():
    m_open = mock_open(read_data=valid_pyproject_toml)
    with patch("builtins.open", m_open), \
         patch("os.path.exists", return_value=False):
        name, desc, version = read_pyproject_metadata()
        assert name == "Test API"
        assert desc == "A test API description"
        assert version == "0.1.1"  # default fallback

def test_read_pyproject_metadata_missing_pyproject_file():
    with patch("builtins.open", side_effect=FileNotFoundError), \
         patch("os.path.exists", return_value=False):
        name, desc, version = read_pyproject_metadata()
        assert name == "CRUD API"  # default fallback
        assert desc == "A secure CRUD API with JWT authentication"  # default fallback
        assert version == "0.1.1"  # default fallback

def test_read_pyproject_metadata_malformed_pyproject():
    m_open = mock_open(read_data=invalid_pyproject_toml)
    with patch("builtins.open", m_open), \
         patch("os.path.exists", return_value=False):
        # tomllib.load will raise TOMLDecodeError (subclass of ValueError)
        name, desc, version = read_pyproject_metadata()
        # Should fallback to defaults
        assert name == "CRUD API"
        assert desc == "A secure CRUD API with JWT authentication"
        assert version == "0.1.1"

def test_read_pyproject_metadata_empty_fields():
    empty_fields_pyproject_toml = b"[project]\nname = \"\"\ndescription = \"\"\n"
    m_open = mock_open()
    # Mock pyproject.toml with empty strings and a version file
    m_open.side_effect = [
        mock_open(read_data=empty_fields_pyproject_toml).return_value,
        mock_open(read_data="").return_value
    ]
    with patch("builtins.open", m_open), patch("os.path.exists", return_value=True):
        name, desc, version = read_pyproject_metadata()
        assert name == "CRUD API"  # fallback default because of empty string
        assert desc == "A secure CRUD API with JWT authentication"  # fallback
        assert version == "0.1.1"  # fallback due to empty version content
