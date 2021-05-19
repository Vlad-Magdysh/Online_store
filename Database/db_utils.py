from flask import g
import sqlite3 as sq

DATABASE = 'production.sqlite'


def dict_factory(cursor, row):
    """
    Format sqlite row to dictionary
    :param cursor: cursor for the connection to sqlite database
    :param row: sqlite row
    :return: Dictionary representation of a row
    """
    items = {}
    for idx, col in enumerate(cursor.description):
        items[col[0]] = row[idx]
    return items


def get_db():
    """
    Return the connection if it exists in the application context,
    else - connects to the database, writes to application context and then return connection
    :return: Connection - SQLite database connection object
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = sq.connect(DATABASE)
        g.sqlite_db.row_factory = dict_factory
    return g.sqlite_db

