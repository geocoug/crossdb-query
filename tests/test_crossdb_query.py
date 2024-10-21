#!/usr/bin/env python

import logging
import os
from unittest.mock import patch

import psycopg2
import pytest
from dotenv import load_dotenv
from psycopg2.sql import SQL, Literal

from crossdb_query import PostgresDB

load_dotenv()

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def global_variables():
    """Set global variables for the test session."""
    return {
        "POSTGRES_HOST": os.getenv("POSTGRES_HOST", "localhost"),
        "POSTGRES_PORT": os.getenv("POSTGRES_PORT", 5432),
        "POSTGRES_DB": os.getenv("POSTGRES_DB", "postgres"),
        "POSTGRES_USER": os.getenv("POSTGRES_USER", "postgres"),
        "POSTGRES_PASSWORD": os.getenv("POSTGRES_PASSWORD", "postgres"),
    }


@pytest.fixture(scope="session")
def db(global_variables):
    """Return a PostgresDB object."""
    db = PostgresDB(
        host=global_variables["POSTGRES_HOST"],
        database=global_variables["POSTGRES_DB"],
        user=global_variables["POSTGRES_USER"],
        passwd=global_variables["POSTGRES_PASSWORD"],
    )
    yield db
    db.close()


def test_db_connection(db):
    """Test the database connection is successful, then close it."""
    assert db.conn is None
    db.open_db()
    assert db.conn is not None
    db.close()
    assert db.conn is None


def test_db_execute(db):
    """Test a simple query execution."""
    cur = db.execute("SELECT 1")
    assert cur.fetchone()[0] == 1


def test_db_execute_values(db):
    """Test a query execution with values."""
    cur = db.execute(SQL("SELECT {}").format(Literal(1)))
    assert cur.fetchone()[0] == 1
    cur = db.execute(
        SQL("""select {value};""").format(
            value=Literal("test_value"),
        ),
    )
    assert cur.fetchone()[0] == "test_value"


def test_valid_connection_success(db):
    """Test the valid_connection method."""
    with (
        patch.object(db, "open_db", return_value=None) as mock_open_db,
        patch.object(db, "close", return_value=None) as mock_close,
    ):
        assert db.valid_connection() is True
        mock_open_db.assert_called_once()
        mock_close.assert_called_once()


def test_valid_connection_failure(db):
    """Test that the valid_connection method fails."""
    db.user = "wrong_user"
    with (
        patch.object(db, "open_db", side_effect=psycopg2.Error) as mock_open_db,
        patch.object(db, "close", return_value=None) as mock_close,
    ):
        assert db.valid_connection() is False
        mock_open_db.assert_called_once()
        mock_close.assert_called_once()


# Run the tests
if __name__ == "__main__":
    pytest.main()
