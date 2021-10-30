import mock
import os
from koala.utils.KoalaUtils import __parse_args, get_arg_config_path, format_config_path


@mock.patch("koala.utils.KoalaUtils.CONFIG_PATH", "/config/")
def test_get_config_from_argv_windows_relative():
    assert get_arg_config_path() == os.getcwd()+"\\config"


@mock.patch("koala.utils.KoalaUtils.CONFIG_PATH", "/config")
def test_get_config_from_argv_windows_relative_partial():
    assert get_arg_config_path() == os.getcwd()+"\\config"


@mock.patch("koala.utils.KoalaUtils.CONFIG_PATH", "\\config\\")
def test_get_config_from_argv_windows_relative_backslash():
    assert get_arg_config_path() == os.getcwd()+"\\config"


@mock.patch("koala.utils.KoalaUtils.CONFIG_PATH", "/test/config/")
def test_get_config_from_argv_windows_absolute():
    assert get_arg_config_path() == os.getcwd()+"\\test\\config"


def test_parse_args_config():
    assert "/config/" == vars(__parse_args(["--config", "/config/"])).get("config")


def test_parse_args_invalid():
    assert vars(__parse_args(["--test", "/test/"])).get("config") is None


@mock.patch("os.name", "posix")
def test_format_db_path_linux_absolute():
    db_path = format_config_path("/test_dir/", "test.db")
    assert db_path == "/test_dir/test.db"


@mock.patch("os.name", "nt")
def test_format_db_path_windows():
    db_path = format_config_path("/test_dir/", "windows_test.db")
    assert db_path == "\\test_dir\\windows_test.db"
