from flask import Blueprint, request, render_template, url_for, g, session, redirect, abort, flash
from Database.db_utils import get_db

admin = Blueprint('admin', __name__, template_folder='admin', url_prefix='/admin')


@admin.route('/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == "GET":
        if session.get('admin'):
            return redirect(url_for('admin.main_admin'))
        return render_template('login.html')
    elif request.method == "POST":
        if fields := request.form.to_dict():
            query = f"""
            SELECT * FROM admins
            WHERE admin_email = '{fields['email']}' and password = '{fields['password']}'
            """
            db_cursor = get_db().cursor()
            db_cursor.execute(query)
            if db_cursor.fetchone():
                session['admin'] = True
                return redirect(url_for('admin.main_admin'))
            else:
                return redirect(url_for('admin.admin_login'))
        else:
            return redirect(url_for('admin.admin_login'))


@admin.route('/main', methods=['GET', 'POST'])
def main_admin():
    if request.method == "GET":
        if session.get('admin'):
            query = """
            SELECT id, user_email, status
            FROM orders
            """
            db_cursor = get_db().cursor()
            db_cursor.execute(query)
            orders = db_cursor.fetchall()
            query = """
            SELECT user_email, description
            FROM letters
            """
            db_cursor.execute(query)
            letters = db_cursor.fetchall()
            return render_template('main_admin.html', orders=orders, letters=letters)
        else:
            abort(404)
    elif request.method == "POST":
        pass


@admin.route('/id-<id_>-<email>', methods=['GET', 'POST'])
def order(id_, email):
    if session.get('admin'):
        if request.method == "GET":
            query = f"""
            SELECT name, surname, city, mail_index, email, phone
            FROM users
            WHERE email == '{email}'
            """
            db_cursor = get_db().cursor()
            db_cursor.execute(query)
            user = db_cursor.fetchone()

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
            return render_template('order_template.html', user=user, products=products, order_price=order_price
                                   , status=order_['status'], id_=id_)
        elif request.method == "POST":
            status = request.form['status']
            query = f"""
            UPDATE orders
            SET status={status}
            WHERE id == {id_}
            """
            db_cursor = get_db().cursor()
            db_cursor.execute(query)
            get_db().commit()
            return redirect(url_for('admin.order', id_=id_, email=email))


@admin.route('/base-products', methods=['GET', 'POST'])
def all_products():
    if session.get('admin'):
        if request.method == "GET":
            query = """
            SELECT * 
            FROM products
            """
            db_cursor = get_db().cursor()
            db_cursor.execute(query)
            if not (products := db_cursor.fetchall()):
                products = []
            return render_template('all_products.html', products=products)
        elif request.method == "POST":
            fields = request.form.to_dict()
            db_cursor = get_db().cursor()
            for key, value in fields.items():
                query = f"""
                UPDATE products
                SET quantity = {value}
                WHERE id == {int(key)}
                """
                db_cursor.execute(query)
            get_db().commit()
            return redirect(url_for('admin.all_products'))


@admin.route('/add-product', methods=['GET', 'POST'])
def add_product():
    if session.get('admin'):
        if request.method == "GET":
            return render_template('add_product.html')
        elif request.method == "POST":
            if fields := request.form.to_dict():
                query = f"""
                INSERT INTO products 
                (image, category, name, price, quantity, country, description) 
                VALUES ( '{fields['image']}', '{fields['category']}', '{fields['name']}', {fields['price']}, {fields['quantity']}, '{fields['country']}', '{fields['description']}' )
                """
                db_cursor = get_db().cursor()
                db_cursor.execute(query)
                get_db().commit()
                return redirect(url_for('admin.all_products'))
            else:
                return redirect(url_for('admin.add_product'))
