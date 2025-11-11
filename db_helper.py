"""
Database Helper Module for EDSDEVV
Provides context manager for safe database connection handling
"""

from contextlib import contextmanager
import psycopg2
import os

# Get database URL from environment or fallback to default
external_database_url = os.getenv(
    'DATABASE_URL',
    "postgresql://lmsdatabase_8ag3_user:6WD9lOnHkiU7utlUUjT88m4XgEYQMTLb@dpg-ctp9h0aj1k6c739h9di0-a.oregon-postgres.render.com/lmsdatabase_8ag3"
)


@contextmanager
def get_db():
    """
    Context manager for database connections.
    
    Automatically opens a connection, yields a cursor, and ensures
    proper cleanup (commit/rollback) and connection closure.
    
    Usage:
        with get_db() as (cursor, connection):
            cursor.execute("SELECT * FROM table WHERE id = %s", (123,))
            result = cursor.fetchone()
            connection.commit()
    
    Guarantees:
    - Connection is closed after use (finally block)
    - Cursor is closed after use (finally block)
    - No connection leaks on exceptions
    """
    connection = None
    cursor = None
    try:
        connection = psycopg2.connect(external_database_url)
        cursor = connection.cursor()
        yield cursor, connection
    except Exception as e:
        if connection:
            connection.rollback()
        raise e
    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass  # Ignore errors during cursor close
        if connection:
            try:
                connection.close()
            except Exception:
                pass  # Ignore errors during connection close


@contextmanager
def get_db_cursor_only():
    """
    Simplified context manager that yields only cursor.
    
    Usage:
        with get_db_cursor_only() as cursor:
            cursor.execute("SELECT * FROM table")
            results = cursor.fetchall()
    
    Note: Remember to manually commit if doing writes!
    """
    connection = None
    cursor = None
    try:
        connection = psycopg2.connect(external_database_url)
        cursor = connection.cursor()
        yield cursor
    except Exception as e:
        if connection:
            connection.rollback()
        raise e
    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        if connection:
            try:
                connection.close()
            except Exception:
                pass


def execute_query(query, params=None, fetch_one=False, fetch_all=False, commit=False):
    """
    Helper function for single queries (non-context-based).
    
    Args:
        query: SQL query string
        params: Tuple of parameters for the query
        fetch_one: If True, returns one result
        fetch_all: If True, returns all results
        commit: If True, commits the transaction
    
    Returns:
        Query result or None depending on fetch flags
    
    Example:
        result = execute_query("SELECT * FROM users WHERE id = %s", (1,), fetch_one=True)
    """
    with get_db() as (cursor, connection):
        cursor.execute(query, params or ())
        
        if fetch_one:
            result = cursor.fetchone()
        elif fetch_all:
            result = cursor.fetchall()
        else:
            result = None
        
        if commit:
            connection.commit()
        
        return result
