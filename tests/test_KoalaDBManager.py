#!/usr/bin/env python

"""
Testing KoalaBot Database Manager

Commented using reStructuredText (reST)
"""
# Futures

# Built-in/Generic Imports
import os

# Libs
import pytest
import mock

# Own modules
from utils import KoalaDBManager

# Constants

# Variables


@mock.patch("os.name", "nt")
def test_format_db_path_windows_absolute_full():
    db_path = KoalaDBManager.format_db_path("C:/test_dir/", "test.db")
    assert db_path == "C:/test_dir/windows_test.db"


@mock.patch("os.name", "nt")
def test_format_db_path_windows_absolute_partial():
    db_path = KoalaDBManager.format_db_path("C:/test_dir", "test.db")
    assert db_path == "C:/test_dir/windows_test.db"


@mock.patch("os.name", "nt")
@mock.patch("os.getcwd", mock.MagicMock(return_value="C:/"))
def test_format_db_path_windows_relative_full():
    db_path = KoalaDBManager.format_db_path("/test_dir/", "test.db")
    assert db_path == "C:/test_dir/windows_test.db"


@mock.patch("os.name", "nt")
@mock.patch("os.getcwd", mock.MagicMock(return_value="C:/"))
def test_format_db_path_windows_relative_backslash():
    db_path = KoalaDBManager.format_db_path("\\test_dir\\", "test.db")
    assert db_path == "C:/test_dir/windows_test.db"


@mock.patch("os.name", "nt")
@mock.patch("os.getcwd", mock.MagicMock(return_value="C:/"))
def test_format_db_path_windows_relative_partial():
    db_path = KoalaDBManager.format_db_path("test_dir/", "test.db")
    assert db_path == "C:/test_dir/windows_test.db"


@mock.patch("os.name", "posix")
@mock.patch("utils.KoalaDBManager.ENCRYPTED_DB", False)
def test_format_db_path_linux_absolute_unencrypted():
    db_path = KoalaDBManager.format_db_path("/test_dir/", "test.db")
    assert db_path == "/test_dir/windows_test.db"


@mock.patch("os.name", "posix")
@mock.patch("utils.KoalaDBManager.ENCRYPTED_DB", True)
def test_format_db_path_linux_absolute_encrypted():
    db_path = KoalaDBManager.format_db_path("/test_dir/", "test.db")
    assert db_path == "/test_dir/test.db"


@mock.patch("os.name", "posix")
@mock.patch("utils.KoalaDBManager.ENCRYPTED_DB", True)
def test_format_db_path_linux_relative():
    db_path = KoalaDBManager.format_db_path("test_dir/", "test.db")
    assert db_path == "test_dir/test.db"

