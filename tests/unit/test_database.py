"""Unit tests for database module (e.g. _db_name_from_uri)."""
import pytest
from database import _db_name_from_uri


def test_db_name_from_uri_simple():
    assert _db_name_from_uri("mongodb://localhost:27017/iot_security") == "iot_security"


def test_db_name_from_uri_with_options():
    u = "mongodb://localhost:27017/my_db?retryWrites=true"
    assert _db_name_from_uri(u) == "my_db"


def test_db_name_from_uri_atlas():
    u = "mongodb+srv://user:pass@cluster.mongodb.net/production"
    assert _db_name_from_uri(u) == "production"


def test_db_name_from_uri_no_path():
    assert _db_name_from_uri("mongodb://localhost:27017") == "iot_security"


def test_db_name_from_uri_root_path():
    assert _db_name_from_uri("mongodb://localhost:27017/") == "iot_security"


def test_db_name_from_uri_invalid():
    assert _db_name_from_uri("not-a-uri") == "iot_security"
