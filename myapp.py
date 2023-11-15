from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from flask import flash


app = Flask(__name__)

app.secret_key = 'your_secret_key'

# Konfigurasi koneksi database
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'  
app.config['MYSQL_PASSWORD'] = ''  
app.config['MYSQL_DB'] = 'inventory-responsi'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

def is_logged_in():
    return 'username' in session

def redirect_if_not_logged_in(route):
    if not is_logged_in():
        return redirect(url_for(route))
    
@app.route('/')
def index():
    if not is_logged_in():
        return redirect(url_for('login'))  # Redirect ke halaman login jika belum login
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM inventories")
    inventory = cur.fetchall()

    # Calculate category counts
    categories = {}
    quantity_data = {}  # Dictionary untuk menyimpan kuantitas barang per kategori

    for item in inventory:
        category = item['kategori']
        categories[category] = categories.get(category, 0) + 1

        # Hitung kuantitas barang (gantilah 'jumlah' dengan kolom yang sesuai pada tabel inventories)
        quantity_data[category] = quantity_data.get(category, 0) + item['jumlah']

    cur.close()

    # Pastikan categories dan quantity_data tidak kosong sebelum mengirimkannya ke template
    categories = categories if categories else {}
    quantity_data = quantity_data if quantity_data else {}

    return render_template('index.html', inventory=inventory, categories=categories, quantity_data=quantity_data)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user['password'], password):
            session['username'] = username
            return redirect(url_for('index'))
        else:
            error = 'Invalid username or password'

    return render_template('login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        fullname = request.form['fullname']
        email = request.form['email']
        address = request.form['address']
        phone = request.form['phone']

        # Meng-generate hashed password menggunakan generate_password_hash
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (username, password, fullname, email, address, phone) VALUES (%s, %s, %s, %s, %s, %s)",
                    (username, hashed_password, fullname, email, address, phone))
        mysql.connection.commit()
        cur.close()

        session['username'] = username
        return redirect(url_for('index'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    if is_logged_in():
        username = session['username']
        session.clear()
        flash(f'Pengguna {username} telah logout', 'success')
    return redirect(url_for('login'))


# route inventory
@app.route('/inventory')
def inventory():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM inventories")
    inventory = cur.fetchall()
    cur.close()

    categories = []
    category_counts = {}

    for item in inventory:
        category = item['kategori']
        if category not in categories:
            categories.append(category)
            category_counts[category] = 1
        else:
            category_counts[category] += 1

    return render_template('inventory.html', inventory=inventory, categories=categories, category_counts=category_counts)


@app.route('/add_category', methods=['GET', 'POST'])
def add_category():
    if request.method == 'POST':
        category_name = request.form['categoryName']

        # Perform database insertion or update to add the new category
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO categories (name) VALUES (%s)", (category_name,))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('inventory'))  # Redirect to the inventory page after adding the category

    return render_template('add_category.html')

@app.route('/add_item', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        nama = request.form['nama']
        kategori = request.form['kategori']
        jumlah = request.form['jumlah']
        harga_beli = request.form['harga_beli']
        harga_jual = request.form['harga_jual']
        keterangan = request.form['keterangan']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO inventories (nama, kategori, jumlah, harga_beli, harga_jual, keterangan) VALUES (%s, %s, %s, %s, %s, %s)",
                    (nama, kategori, jumlah, harga_beli, harga_jual, keterangan))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('inventory'))

    return render_template('add_item.html')

@app.route('/view_item/<int:id>')
def view_item(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM inventories WHERE id = %s", (id,))
    item = cur.fetchone()
    cur.close()
    return render_template('view_item.html', item=item)

@app.route('/edit_item/<int:id>', methods=['GET', 'POST'])
def edit_item(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM inventories WHERE id = %s", (id,))
    item = cur.fetchone()

    if request.method == 'POST':
        nama = request.form['nama']
        kategori = request.form['kategori']
        jumlah = request.form['jumlah']
        harga_beli = request.form['harga_beli']
        harga_jual = request.form['harga_jual']
        keterangan = request.form['keterangan']

        cur = mysql.connection.cursor()
        cur.execute("UPDATE inventories SET nama=%s, kategori=%s, jumlah=%s, harga_beli=%s, harga_jual=%s, keterangan=%s WHERE id=%s",
                    (nama, kategori, jumlah, harga_beli, harga_jual, keterangan, id))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('inventory'))

    return render_template('edit_item.html', item=item)

@app.route('/delete_item/<int:id>')
def delete_item(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM inventories WHERE id = %s", (id,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('inventory'))

if __name__ == '__main__':
    app.run(debug=True)
