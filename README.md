# crossdb-query

[![python tests](https://github.com/geocoug/crossdb-query/actions/workflows/python-tests.yaml/badge.svg)](https://github.com/geocoug/crossdb-query/actions/workflows/python-tests.yaml)
[![docker build](https://github.com/geocoug/crossdb-query/actions/workflows/docker-build.yaml/badge.svg)](https://github.com/geocoug/crossdb-query/actions/workflows/docker-build.yaml)
[![pypi publish](https://github.com/geocoug/crossdb-query/actions/workflows/pypi-publish.yaml/badge.svg)](https://github.com/geocoug/crossdb-query/actions/workflows/pypi-publish.yaml)

Execute a SQL file on all PostgreSQL databases on a host. By default, the script will execute the SQL file on all databases on the host. The user can specify a list of databases to include or exclude from the execution. By default, the postgres database is excluded from the execution as well as any template databases.

## Features

- Execute SQL files on multiple PostgreSQL databases.
- Include or exclude specific databases.
- List all available databases on the host.
- Debug logging support.

## Installation

### Using Docker

1. Build the Docker image:

    ```sh
    docker build -t crossdb-query .
    ```

2. Run the Docker container and bind mount the SQL file:

    ```sh
    docker run -it --rm -v $(pwd)/<sql_file>:/app/<sql_file> crossdb-query -u <username> -v <host> -f <sql_file>
    ```

### Using Python

1. Install using pip:

    ```sh
    pip install crossdb-query
    ```

2. Run the script:

    ```sh
    crossdb_query.py -u <username> -v <host> -f <sql_file>
    ```

## Usage

```sh
usage: crossdb_query.py [-h] [-d] [-f FILE] -u USER -v HOST [-p PORT] [-l] [-i INCLUDE] [-e EXCLUDE]

Execute a SQL file on all PostgreSQL databases on a host. By default, the script will execute the SQL file on all databases on the host. The user can specify a list of databases to include or exclude from the execution.

options:
  -h, --help            show this help message and exit
  -d, --debug           Enable debug logging.
  -f FILE, --file FILE  The SQL file to execute.
  -u USER, --user USER  The username to connect to the database.
  -v HOST, --host HOST  The host of the database.
  -p PORT, --port PORT  The port of the database.
  -l, --list            List all available databases on the host and exit.
  -i INCLUDE, --include INCLUDE
                        A comma-separated list of databases on which the SQL file will be executed. THe databases must be separated by a comma and no spaces.
  -e EXCLUDE, --exclude EXCLUDE
                        A comma-separated list of databases on which the SQL file will not be executed. The databases must be separated by a comma and no spaces.
```

## Examples

### List all databases on the host

```sh
$ crossdb_query.py -u <username> -v <host> -l

The script crossdb_query.py wants the password for PostgresDB(host=localhost, port=5432, database=postgres, user=pg_user):
Available databases:
  - accounts
  - customers
  - django_db
  - employees
```

### Execute a SQL file on selected databases

```sh
$ crossdb_query.py -u <username> -v <host> -f <sql_file> -i accounts,employees

The script crossdb_query.py wants the password for PostgresDB(host=localhost, port=5432, database=postgres, user=pg_user):
Databases selected for execution:
  - accounts
  - employees
(1/2) Executing on database accounts
  Success
(2/2) Executing on database employees
  Success
```

### Execute a SQL file on all databases except the specified ones

```sh
$ crossdb_query.py -u <username> -v <host> -f <sql_file> -e accounts,employees

The script crossdb_query.py wants the password for PostgresDB(host=localhost, port=5432, database=postgres, user=pg_user):
Databases selected for execution:
  - customers
  - django_db
(1/2) Executing on database customers
  Success
(2/2) Executing on database django_db
  Success
```

## Notes

If the user specifies a database that does not exist on the host, the script will ignore the database and continue with the script execution without warning the user.
