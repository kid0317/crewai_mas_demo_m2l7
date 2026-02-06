"""配置与安全单元测试。"""

import pytest

from app.core.config import Settings, get_settings


def test_settings_defaults() -> None:
    s = Settings()
    assert s.env == "development"
    assert s.port == 8072
    assert s.log_level == "INFO"


def test_get_valid_api_keys_empty() -> None:
    s = Settings(api_keys="")
    assert s.get_valid_api_keys() == set()


def test_get_valid_api_keys() -> None:
    s = Settings(api_keys=" key1 , key2 ")
    assert s.get_valid_api_keys() == {"key1", "key2"}


def test_get_settings_cached() -> None:
    a = get_settings()
    b = get_settings()
    assert a is b
