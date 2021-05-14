from flask import Flask, render_template, g
import sqlite3 as sq

DATABASE = 'production.sqlite'
DEBUG = True
SECRET_KEY = b'\xa7\xf9\x85\xac \x85\xccL\xeb\xb8\xcd\xcb\xe7Ey\xeb\xc1\xa2~E'

app = Flask(__name__)
app.config.from_object(__name__)


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
        g.sqlite_db = sq.connect(app.config['DATABASE'])
        g.sqlite_db.row_factory = dict_factory
    return g.sqlite_db


@app.teardown_appcontext
def close_db(self):
    """
    When the application context dies - close the connection to the database if it exist.
    (usually at the end of the request)
    :return: None
    """
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


@app.route('/')
def main_app():
    return render_template('main.html')


@app.route('/delivery-info')
def delivery_info():
    return render_template('delivery_info.html')


@app.route('/news')
def news():
    query = """
    SELECT title, image, date, description
    FROM news
    """
    db_cursor = get_db().cursor()
    db_cursor.execute(query)
    posts = db_cursor.fetchall()
    return render_template('news.html', posts=posts)


if __name__ == '__main__':
    app.run()
