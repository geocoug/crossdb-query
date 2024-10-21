#!/usr/bin/env python3
from __future__ import annotations

import argparse
import logging
from getpass import getpass
from pathlib import Path

import psycopg2
from psycopg2.extras import DictCursor
from psycopg2.sql import Composable

__title__ = "crossdb_query"
__author__ = "Caleb Grant"
__url__ = "https://github.com/geocoug/crossdb-query"
__author_email__ = "grantcaleb22@gmail.com"
__license__ = "GNU GPLv3"
__version__ = "0.0.1"
__description__ = "Execute a SQL file on all PostgreSQL databases on a host. By default, the script will execute the SQL file on all databases on the host. The user can specify a list of databases to include or exclude from the execution."  # noqa


logging.basicConfig(format="%(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


class PostgresDB:
    """Base database object."""

    def __init__(
        self: PostgresDB,
        host: str,
        database: str,
        user: str,
        port: int = 5432,
        passwd: None | str = None,
    ) -> None:
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        if passwd is not None:
            self.passwd = passwd
        else:
            self.passwd = self.get_password()
        self.in_transaction = False
        self.encoding = "UTF8"
        self.conn = None
        if not self.valid_connection():
            raise psycopg2.Error(f"Error connecting to {self!s}")

    def __repr__(self: PostgresDB) -> str:
        return (
            f"{self.__class__.__name__}(host={self.host}, port={self.port}, database={self.database}, user={self.user})"
        )

    def get_password(self):
        try:
            return getpass(
                f"The script {Path(__file__).name} wants the password for {self!s}: ",
            )
        except (KeyboardInterrupt, EOFError) as err:
            raise err

    def valid_connection(self: PostgresDB) -> bool:
        """Test the database connection."""
        logger.debug(f"Testing connection to {self!s}")
        try:
            self.open_db()
            logger.debug(f"Connected to {self!s}")
            return True
        except psycopg2.Error:
            return False
        finally:
            self.close()

    def open_db(self: PostgresDB) -> None:
        """Open a database connection."""

        def db_conn(db) -> psycopg2.extensions.connection:
            """Return a database connection object."""
            return psycopg2.connect(
                host=str(db.host),
                database=str(db.database),
                port=db.port,
                user=str(db.user),
                password=str(db.passwd),
            )

        if self.conn is None:
            self.conn = db_conn(self)
            if self.conn:
                self.conn.set_session(autocommit=False)
            else:
                raise psycopg2.Error(f"Error connecting to {self!s}")
        self.encoding = self.conn.encoding

    def cursor(self: PostgresDB):
        """Return the connection cursor."""
        self.open_db()
        if self.conn is None:
            raise psycopg2.Error(f"Error connecting to {self!s}")
        return self.conn.cursor(cursor_factory=DictCursor)

    def close(self: PostgresDB) -> None:
        """Close the database connection."""
        self.rollback()
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def commit(self: PostgresDB) -> None:
        """Commit the current transaction."""
        if self.conn:
            self.conn.commit()
        self.in_transaction = False

    def rollback(self: PostgresDB) -> None:
        """Roll back the current transaction."""
        if self.conn is not None:
            self.conn.rollback()
        self.in_transaction = False

    def execute(self: PostgresDB, sql: str | Composable, params=None):
        """A shortcut to self.cursor().execute() that handles encoding.

        Handles insert, updates, deletes
        """
        self.in_transaction = True
        try:
            curs = self.cursor()
            if isinstance(sql, Composable):
                logger.debug(sql.as_string(curs))
                curs.execute(sql)
            else:
                if params is None:
                    logger.debug(f"{sql}")
                    curs.execute(sql.encode(self.encoding))
                else:
                    logger.debug(f"SQL:\n{sql}\nParameters:\n{params}")
                    curs.execute(sql.encode(self.encoding), params)
        except Exception:
            self.rollback()
            raise
        return curs


def clparser() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description=__description__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        required=False,
        help="Enable debug logging.",
    )
    parser.add_argument(
        "-f",
        "--file",
        type=str,
        required=False,
        help="The SQL file to execute.",
    )
    parser.add_argument(
        "-u",
        "--user",
        type=str,
        required=True,
        help="The username to connect to the database. ",
    )
    parser.add_argument(
        "-v",
        "--host",
        type=str,
        required=True,
        help="The host of the database.",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        required=False,
        default=5432,
        help="The port of the database.",
    )
    parser.add_argument(
        "-l",
        "--list",
        action="store_true",
        required=False,
        help="List all available databases on the host and exit.",
    )
    parser.add_argument(
        "-i",
        "--include",
        type=str,
        required=False,
        help="A comma-separated list of databases on which the SQL file will be executed. THe databases must be separated by a comma and no spaces.",  # noqa
    )
    parser.add_argument(
        "-e",
        "--exclude",
        type=str,
        required=False,
        help="A comma-separated list of databases on which the SQL file will not be executed. The databases must be separated by a comma and no spaces.",  # noqa
    )
    return parser.parse_args()


def main() -> None:
    args = clparser()
    if args.debug:
        logger.setLevel(logging.DEBUG)
    db = PostgresDB(
        host=args.host,
        database="postgres",
        user=args.user,
        port=args.port,
    )
    cur = db.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
    databases = [row["datname"] for row in sorted(cur.fetchall())]
    if args.list:
        logger.info("Available databases:")
        for database in databases:
            logger.info(f"  - {database}")
        return
    if not args.file:
        logger.error("No SQL file provided.")
        return
    try:
        sql = Path(args.file).read_text()
    except FileNotFoundError as err:
        raise err
    except Exception as err:
        raise err
    if args.include:
        databases = [database for database in databases if database in args.include.split(",")]
    if args.exclude:
        databases = [database for database in databases if database not in args.exclude.split(",")]
    if not databases:
        logger.error("No databases selected for execution.")
        return
    logger.info("Databases selected for execution:")
    for database in databases:
        logger.info(f"  - {database}")
    for n, database in enumerate(databases):
        db.database = database
        logger.info(
            f"({n + 1:0{len(str(len(databases)))}}/{len(databases)}) Executing on database {database}",
        )
        try:
            db.execute(sql)
            db.commit()
            logger.info("  Success")
        except Exception as err:
            logger.error(err)
            db.rollback()
    db.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt as err:
        raise err
    except Exception as err:
        raise err
