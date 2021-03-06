from flask import Flask, render_template, g, request, session, redirect, url_for, flash, abort, jsonify, Blueprint
from flask_cors import CORS
from Validator.user_validate import Validate
from admin_blueprint import admin
from Database.db_utils import get_db
DATABASE = 'production.sqlite'
DEBUG = True
SECRET_KEY = b'\xa7\xf9\x85\xac \x85\xccL\xeb\xb8\xcd\xcb\xe7Ey\xeb\xc1\xa2~E'

app = Flask(__name__)
app.config.from_object(__name__)
app.register_blueprint(admin)
CORS(app)


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


@app.route('/catalog-<string:product_type>', methods=['GET', 'POST'])
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
    url_catalog = f'/catalog-{product_type}'
    if request.method == "GET":
        query = f"""
        SELECT id, image, name, price
        FROM products
        WHERE category== '{product_type}'
        """
        db_cursor.execute(query)
        products = db_cursor.fetchall()

        for item in products:
            item['image'] = f"{product_type}/{item.get('image', '')}"

        return render_template("catalog_template.html", kinds=kinds, countries=countries,
                               products=products, url_catalog=url_catalog)
    elif request.method == "POST":
        fields = request.form.to_dict()
        if not (lower_price := fields.get('lower_price')):
            lower_price = 0
        if not (upper_price := fields.get('upper_price')):
            upper_price = 99999
        selected_kinds = [item.removeprefix('kind-') for item in fields.keys() if item.startswith('kind-')]
        query = f"""
        SELECT * 
        FROM products
        WHERE category == '{product_type}'
        AND
        price BETWEEN {lower_price} and {upper_price}
        """
        if selected_kinds:
            str_kinds = '\' , \''.join(selected_kinds)
            query += f"""AND
        filters in ('{str_kinds}')
            """
        selected_counties = [item.removeprefix('country-') for item in fields.keys() if item.startswith('country-')]
        if selected_counties:
            str_counties = '\' , \''.join(selected_counties)
            query += f"""AND
        country in ('{str_counties}')
            """
        print(query)
        db_cursor.execute(query)
        products = db_cursor.fetchall()
        for item in products:
            item['image'] = f"{product_type}/{item.get('image', '')}"
        return render_template("catalog_template.html", kinds=kinds, countries=countries,
                               products=products, url_catalog=url_catalog)


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
        selected = dict(session.items())
        selected.pop('logged_in', True)
        selected.pop('admin', True)
        ids = selected.keys()
        query = f"""
        SELECT *
        FROM products
        WHERE id in ({', '.join([item for item in ids])})
        """
        db_cursor = get_db().cursor()
        db_cursor.execute(query)
        products = db_cursor.fetchall()
        for product_ in products:
            product_['image'] = f"{product_['category']}/{product_.get('image', '')}"
            product_['number'] = selected[f'{product_["id"]}']
        return render_template("basket.html", products=products, len=len(products))
    elif request.method == "POST":
        fields = request.form.to_dict()
        value = list(fields.values())[0]
        session.pop(value, None)
        return redirect(url_for('basket'))


@app.route('/contact-us', methods=['GET', 'POST'])
def contact():
    if request.method == "GET":
        return render_template("contacts.html")
    if request.method == "POST":
        if not (request.form.get('name') and request.form.get('phone') and request.form.get('email')
                and request.form.get('message') and request.form.get('answer')):
            flash("?????????????? ???? ?????? ????????????! ?????????????????? ???? ????????????????????!")
        elif request.form.get('answer').strip() != "54":
            flash("???????????????? ?? ??????????????????????! ?????????????????? ???? ????????????????????!")
        else:
            query = f"""
            INSERT INTO letters (user_name, user_phone, user_email, description, status)
            VALUES ('{request.form.get('name')}', '{request.form.get('phone')}', '{request.form.get('email')}', '{request.form.get('message')}', 0)
            """
            db_cursor = get_db().cursor()
            db_cursor.execute(query)
            get_db().commit()
            flash("?????????????????? ?????????????? ??????????????????????. ?????? ???????????????? ?????????????? ?????? ?????? ????????????!")
        return redirect(url_for('contact'))


@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if request.method == "GET":
        if session.get('logged_in'):
            return redirect(url_for('user', email=session['logged_in']['email']))
        return render_template("registration_page.html")
    elif request.method == "POST":
        fields = request.form.to_dict()
        if not (name := fields.get('name')) or not Validate.name(name):
            flash("?????????????? ?????????????? ??????! ?????????????? 1 ?????????? ?? ?????????????? ??????????.")
        elif not (surname := fields.get('surname')) or not Validate.name(surname):
            flash("?????????????? ?????????????? ??????????????! ?????????????? 1 ?????????? ?? ?????????????? ??????????.")
        elif not (city := fields.get('city')) or not Validate.name(city):
            flash("?????????????? ???????????? ??????????! ?????????????? 1 ?????????? ?? ?????????????? ??????????.")
        elif not (mail_index := fields.get('mail_index')) or not Validate.mail_index(mail_index):
            flash("?????????????? ???????????? ???????????????? ????????????! ?????????????? 5-???????????????? ??????????.")
        elif not (phone := fields.get('phone')) or not Validate.phone(phone):
            flash("?????????????? ???????????? ?????????? ????????????????! ?????????????? 10-?????????????? ??????????.")
        elif not (email := fields.get('email')) or not Validate.email(email):
            flash("?????????????? ?????????????? ?????????????????????? ??????????!")
        elif not (password := fields.get('password')) or not Validate.password(password):
            flash("???????????? ????????????! ???????????? ???????????? ?????????????????? ?????????????? 8 ????????????????, ???? ??????: 1 ?????????????????? ??????????, 1 ???????????????? ??????????, 1 ??????????")
        elif password != fields.get('confirmed', ""):
            flash("???????????????? ?????????????????????????? ????????????!")
        else:
            query = f"""
            SELECT email 
            FROM users
            WHERE email == '{email}'
            """
            db_cursor = get_db().cursor()
            db_cursor.execute(query)
            if db_cursor.fetchone():
                flash(f"???????????????????????? ?? ?????????? email={email} ?????? ????????????????????")
            else:
                query = f"""
                INSERT INTO users 
                VALUES ('{email}', '{password}', '{phone}', '{name}', '{surname}', '{city}' , '{mail_index}')
                """
                db_cursor.execute(query)
                get_db().commit()
                session['logged_in'] = {'email': email}
                return redirect(url_for('user', email=email))
        return redirect(url_for('registration'))


@app.route('/authorization', methods=['GET', 'POST'])
def authorization():
    if request.method == 'GET':
        return redirect(url_for('registration'))
    elif request.method == 'POST':
        fields = request.form.to_dict()
        query = f"""
        SELECT email
        FROM users
        WHERE email = '{fields.get('email')}' and password == '{fields.get('password')}'
        """
        db_cursor = get_db().cursor()
        db_cursor.execute(query)
        if result := db_cursor.fetchone():
            session['logged_in'] = {'email': result['email']}
            return redirect(url_for('user', email=result['email']))
        else:
            flash("???????????????? ????????????!")
    return redirect(url_for('registration'))


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
    elif request.method == "POST":
        return render_template(url_for('news'))


@app.route('/logged_in', methods=['GET', 'POST'])
def user_logged_in():
    if session.get('logged_in'):
        return jsonify(logged_in=True)
    else:
        return {"logged_in": False}, 204


@app.route('/logged_out', methods=['POST'])
def user_logged_out():
    if session.get('logged_in'):
        session.pop('logged_in', None)
        return {'message': 'User logged out'}, 200
    else:
        return {'message': 'User was not logged in'}, 200


@app.route('/search-result', methods=['POST'])
def search_result():
    if (field := request.form.get('product_name')):
        query = f"""
        SELECT * 
        FROM products
        WHERE name LIKE '%{field}%'
        """
    else:
        query = f"""
        SELECT *
        FROM products
        """

    db_cursor = get_db().cursor()
    db_cursor.execute(query)
    result = db_cursor.fetchall()
    for product_ in result:
        product_['image'] = f"{product_['category']}/{product_.get('image', '')}"
    return render_template('search_template.html', result=result, len=len(result))


@app.route('/make-order', methods=['POST'])
def make_order():
    if email := session.get('logged_in'):
        email = email['email']
        fields = {f"{key.removeprefix('prod_number_')}": value for key, value in request.form.items()}
        if not fields:
            abort(404)
        description = '\n'.join([f"{key} = {value}" for key, value in fields.items()])
        query = f"""
        INSERT INTO orders
        (user_email, description, summary, status)
        VALUES ('{str(email)}', '{description}', 0, 0)
        """
        db_cursor = get_db().cursor()
        db_cursor.execute(query)
        get_db().commit()
        for key, value in fields.items():
            query = f"""
            UPDATE products
            SET quantity = quantity - {value}
            WHERE id == {key}
            """
            db_cursor.execute(query)
        get_db().commit()
        session.clear()
        session['logged_in'] = {'email': email}
        return redirect(url_for('main_app'))


@app.route('/pop-up', methods=['GET', 'POST'])
def delete_user():
    if email := session.get('logged_in'):
        if request.method == "GET":
            return render_template('delete_pop_up.html')
        elif request.method == "POST":
            query = f"""
            DELETE 
            FROM users
            WHERE email == '{email['email']}'
            """
            db_cursor = get_db().cursor()
            db_cursor.execute(query)
            get_db().commit()
            query = f"""
            DELETE 
            FROM orders
            WHERE user_email == '{email['email']}'
            """
            db_cursor.execute(query)
            get_db().commit()
            session.pop('logged_in')
            return "Ok", 200


@app.route('/order-<id_>', methods=['GET'])
def view_order(id_):
    if session.get('logged_in'):
        query = f"""
                    SELECT description, status
                    FROM orders
                    WHERE id == {id_}
                    """
        db_cursor = get_db().cursor()
        db_cursor.execute(query)
        order_ = db_cursor.fetchone()
        archiver_data = order_['description'].split('\n')
        archiver_data = {key: value for key, value in (item.split(' = ') for item in archiver_data)}
        keys = archiver_data.keys()
        query = f"""
                    SELECT id, category, name, price
                    FROM products
                    WHERE id in ({', '.join([item for item in keys])})             
                    """
        db_cursor.execute(query)
        products = db_cursor.fetchall()
        order_price = 0
        for item in products:
            item['number'] = int(archiver_data[str(item['id'])])
            item['total'] = item['number'] * item['price']
            order_price += item['total']
        return render_template('user_order_template.html', products=products, order_price=order_price)


if __name__ == '__main__':
    app.run()
