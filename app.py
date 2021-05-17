from flask import Flask, render_template, g, request, session, redirect, url_for, flash, abort
import sqlite3 as sq
from Validator.user_validate import Validate

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


@app.route('/', methods=['GET'])
def main_app():
    return render_template('main.html')


@app.route('/delivery-info', methods=['GET'])
def delivery_info():
    return render_template('delivery_info.html')


@app.route('/privacy-policy', methods=['GET'])
def privacy_policy():
    return render_template('privacy_policy.html')


@app.route('/news', methods=['GET'])
def news():
    query = """
    SELECT title, image, date, description
    FROM news
    """
    db_cursor = get_db().cursor()
    db_cursor.execute(query)
    posts = db_cursor.fetchall()
    return render_template('news.html', posts=posts)


@app.route('/catalog-<string:product_type>', methods=['GET'])
def catalog(product_type):
    query = f"""
    SELECT weight, name 
    FROM filters
    WHERE product == '{product_type}' AND category == 'kind'
    """
    db_cursor = get_db().cursor()
    db_cursor.execute(query)
    kinds = db_cursor.fetchall()

    query = f"""
    SELECT weight, name 
    FROM filters
    WHERE product == '{product_type}' AND category == 'country'
    """
    db_cursor.execute(query)
    countries = db_cursor.fetchall()

    query = f"""
    SELECT id, image, name, price
    FROM products
    WHERE category== '{product_type}'
    """
    db_cursor.execute(query)
    products = db_cursor.fetchall()

    for item in products:
        item['image'] = f"{product_type}/{item.get('image', '')}"

    return render_template("catalog_template.html", kinds=kinds, countries=countries, products=products)


@app.route('/product-<id_>', methods=['GET', 'POST'])
def product(id_):
    if request.method == "GET":
        query = f"""
            SELECT id, image, category ,name, price, quantity, country, description
            FROM products
            WHERE id == '{id_}'
            """
        db_cursor = get_db().cursor()
        db_cursor.execute(query)
        product_ = db_cursor.fetchone()
        product_['image'] = f"{product_['category']}/{product_.get('image', '')}"
        return render_template("product_template.html", product=product_)
    elif request.method == "POST":
        if session.get(f"{id_}"):
            session[f"{id_}"] += int(request.form.get('prod_number'))
            if int(request.form.get(f"{id_}")) <= session[f"{id_}"]:
                session[f"{id_}"] = int(request.form.get(f"{id_}"))
        else:
            session[f"{id_}"] = int(request.form.get('prod_number'))
        return redirect(url_for('product', id_=id_))


@app.route('/basket', methods=['GET', 'POST'])
def basket():
    if request.method == "GET":
        selected = {}
        selected = dict(session.items())
        if selected.get('logged_in'):
            selected.pop('logged_in')
        ids = selected.keys()
        query = f"""
        SELECT *
        FROM products
        WHERE id in ({', '.join([item for item in ids])})
        """
        print(query)
        db_cursor = get_db().cursor()
        db_cursor.execute(query)
        products = db_cursor.fetchall()
        for product_ in products:
            product_['image'] = f"{product_['category']}/{product_.get('image', '')}"
            product_['number'] = selected[f'{product_["id"]}']
        return render_template("basket.html", products=products, len=len(products))


@app.route('/contact-us', methods=['GET', 'POST'])
def contact():
    if request.method == "GET":
        return render_template("contacts.html")
    if request.method == "POST":
        if not (request.form.get('name') and request.form.get('phone') and request.form.get('email')
                and request.form.get('message') and request.form.get('answer')):
            flash("Введены не все данные! Сообщение не отправлено!")
        elif request.form.get('answer').strip() != "54":
            flash("Проблемы с математикой! Сообщение не отправлено!")
        else:
            query = f"""
            INSERT INTO letters (user_name, user_phone, user_email, description, status)
            VALUES ('{request.form.get('name')}', '{request.form.get('phone')}', '{request.form.get('email')}', '{request.form.get('message')}', 0)
            """
            print(query)
            db_cursor = get_db().cursor()
            db_cursor.execute(query)
            get_db().commit()
            flash("Сообщение успешно отправленно. Наш оператор ответит вам как сможет!")
        return redirect(url_for('contact'))


@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if request.method == "GET":
        if session.get('logged_in'):
            return redirect(url_for('user', email=session['logged_in']['email']))
        return render_template("registration_page.html")
    elif request.method == "POST":
        fields = request.form.to_dict()
        print(fields)
        if not (name := fields.get('name')) or not Validate.name(name):
            flash("Неверно введено имя! Введите 1 слово с большой буквы.")
        elif not (surname := fields.get('surname')) or not Validate.name(surname):
            flash("Неверно введена фамилия! Введите 1 слово с большой буквы.")
        elif not (city := fields.get('city')) or not Validate.name(city):
            flash("Неверно введён город! Введите 1 слово с большой буквы.")
        elif not (mail_index := fields.get('mail_index')) or not Validate.mail_index(mail_index):
            flash("Неверно введён почтовый индекс! Введите 5-цифровое число.")
        elif not (phone := fields.get('phone')) or not Validate.phone(phone):
            flash("Неверно введён номер телефона! Введите 10-значное число.")
        elif not (email := fields.get('email')) or not Validate.email(email):
            flash("Неверно введена электронная почта!")
        elif not (password := fields.get('password')) or not Validate.password(password):
            flash("Слабый пароль! Пароль должен содержать минимум 8 символов, из них: 1 заглавная буква, 1 строчная буква, 1 цифра")
        elif password != fields.get('confirmed', ""):
            flash("Неверное подтверждение пароля!")
        else:
            query = f"""
            SELECT email 
            FROM users
            WHERE email == '{email}'
            """
            db_cursor = get_db().cursor()
            db_cursor.execute(query)
            if db_cursor.fetchone():
                flash(f"Пользователь с таким email={email} уже существует")
            else:
                query = f"""
                INSERT INTO users 
                VALUES ('{email}', '{password}', '{phone}', '{name}', '{surname}', '{city}' , '{mail_index}')
                """
                db_cursor.execute(query)
                get_db().commit()
                session['logged_in'] = {'email': {email}}
                return redirect(url_for('user', email=email))
        return redirect(url_for('registration'))


@app.route('/authorization', methods=['POST'])
def authorization():
    fields = request.form.to_dict()
    query = f"""
    SELECT email
    FROM users
    WHERE email = '{fields.get('email')}' and password == '{fields.get('password')}'
    """
    db_cursor = get_db().cursor()
    db_cursor.execute(query)
    if result := db_cursor.fetchone():
        session['logged_in'] = {'email': {result['email']}}
        return redirect(url_for('user', email=result['email']))
    else:
        flash("Неверные данные!")
        redirect(url_for('registration'))


@app.route('/user-<email>', methods=['GET', "POST"])
def user(email):
    if request.method == "GET":
        if session.get('logged_in'):
            if session['logged_in']['email'] == email:
                query = f"""
                SELECT email, phone, name, surname, city, mail_index
                FROM users
                WHERE email == '{email}'
                """
                db_cursor = get_db().cursor()
                db_cursor.execute(query)
                person = db_cursor.fetchone()
                query = f"""
                SELECT id, status
                FROM orders
                WHERE user_email == '{email}'
                """
                db_cursor.execute(query)
                orders = db_cursor.fetchall()
                return render_template('user_template.html', person=person, orders=orders)
        else:
            abort(404)


if __name__ == '__main__':
    app.run()
