"""Transactions that commit/rollback AND release the Windows database handle."""
from contextlib import contextmanager
import sqlite3


class ClosingConnection(sqlite3.Connection):
    """Also protect callers using the public connect() API as a context."""
    def __exit__(self, *exc):
        try:
            return super().__exit__(*exc)
        finally:
            self.close()


@contextmanager
def transaction(connection):
    try:
        with connection:
            yield connection
    finally:
        connection.close()


@contextmanager
def database_connection(*args, **kwargs):
    with transaction(sqlite3.connect(*args, **kwargs)) as connection:
        yield connection
