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


def test_format_db_path_windows_absolute_full():
    os.name = "nt"
    db_path = KoalaDBManager.format_db_path("C:/test_dir/", "test.db")
    assert db_path == "C:/test_dir/windows_test.db"


def test_format_db_path_windows_absolute_partial():
    os.name = "nt"
    db_path = KoalaDBManager.format_db_path("C:/test_dir", "test.db")
    assert db_path == "C:/test_dir/windows_test.db"


@mock.patch("os.getcwd", mock.MagicMock(return_value="C:/"))
def test_format_db_path_windows_relative_full():
    os.name = "nt"
    db_path = KoalaDBManager.format_db_path("/test_dir/", "test.db")
    assert db_path == "C:/test_dir/windows_test.db"


@mock.patch("os.getcwd", mock.MagicMock(return_value="C:/"))
def test_format_db_path_windows_relative_backslash():
    os.name = "nt"
    db_path = KoalaDBManager.format_db_path("\\test_dir\\", "test.db")
    assert db_path == "C:/test_dir/windows_test.db"


@mock.patch("os.getcwd", mock.MagicMock(return_value="C:/"))
def test_format_db_path_windows_relative_partial():
    os.name = "nt"
    db_path = KoalaDBManager.format_db_path("test_dir/", "test.db")
    assert db_path == "C:/test_dir/windows_test.db"


@mock.patch("utils.KoalaDBManager.os_name", mock.MagicMock(return_value="posix"))
def test_format_db_path_linux_absolute_unencrypted():
    KoalaDBManager.ENCRYPTED_DB = False
    db_path = KoalaDBManager.format_db_path("/test_dir/", "test.db")
    assert db_path == "/test_dir/windows_test.db"


@mock.patch("utils.KoalaDBManager.os_name", mock.MagicMock(return_value="posix"))
@mock.patch("utils.KoalaDBManager.ENCRYPTED_DB", mock.MagicMock(return_value=True))
def test_format_db_path_linux_absolute_encrypted():
    KoalaDBManager.ENCRYPTED_DB = True
    db_path = KoalaDBManager.format_db_path("/test_dir/", "test.db")
    assert db_path == "/test_dir/test.db"


@mock.patch("utils.KoalaDBManager.os_name", mock.MagicMock(return_value="posix"))
@mock.patch("utils.KoalaDBManager.ENCRYPTED_DB", mock.MagicMock(return_value=True))
def test_format_db_path_linux_relative():
    KoalaDBManager.ENCRYPTED_DB = True
    db_path = KoalaDBManager.format_db_path("test_dir/", "test.db")
    assert db_path == "test_dir/test.db"

