from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import os

app = Flask(__name__)
app.config.from_object('config')

mysql = MySQL(app)

# Authentication decorator
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper

# Admin authentication decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first', 'error')
            return redirect(url_for('login'))
            
        cur = mysql.connection.cursor()
        try:
            cur.execute("SELECT is_admin FROM users WHERE id = %s", (session['user_id'],))
            user = cur.fetchone()
            if not user or not user[0]:  # Check if user exists and is admin
                flash('Admin access required', 'error')
                return redirect(url_for('index'))
        finally:
            cur.close()
            
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM products")
    products = cur.fetchall()
    cur.close()
    return render_template('index.html', products=products)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        cur = mysql.connection.cursor()
        try:
            cur.execute("SELECT id, username, password_hash, is_admin FROM users WHERE username = %s", (username,))
            user = cur.fetchone()
            
            if user and check_password_hash(user[2], password):
                session['user_id'] = user[0]
                session['username'] = user[1]
                session['is_admin'] = bool(user[3])  # Properly convert to boolean
                flash('Welcome back!', 'success')
                return redirect(url_for('admin_dashboard') if session['is_admin'] else url_for('index'))
            
            flash('Invalid credentials', 'error')
        finally:
            cur.close()
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        password_hash = generate_password_hash(password)
        
        cur = mysql.connection.cursor()
        try:
            cur.execute("INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                       (username, email, password_hash))
            mysql.connection.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash('Username or email already exists', 'error')
        finally:
            cur.close()
            
    return render_template('register.html')

@app.route('/cart')
@login_required
def cart():
    cur = mysql.connection.cursor()
    try:
        # First check if cart table exists
        cur.execute("""
            SELECT p.*, c.quantity 
            FROM products p 
            INNER JOIN cart c ON p.id = c.product_id 
            WHERE c.user_id = %s
        """, (session['user_id'],))
        cart_items = cur.fetchall()
        return render_template('cart.html', cart_items=cart_items)
    except Exception as e:
        print(f"Cart error: {e}")  # Debug print
        flash('Error loading cart', 'error')
        return redirect(url_for('index'))
    finally:
        cur.close()

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    cur = mysql.connection.cursor()
    try:
        # Check if product already in cart
        cur.execute("SELECT * FROM cart WHERE user_id = %s AND product_id = %s",
                   (session['user_id'], product_id))
        existing_item = cur.fetchone()
        
        if existing_item:
            # Update quantity if product already in cart
            cur.execute("UPDATE cart SET quantity = quantity + 1 WHERE user_id = %s AND product_id = %s",
                       (session['user_id'], product_id))
        else:
            # Add new item to cart
            cur.execute("INSERT INTO cart (user_id, product_id) VALUES (%s, %s)",
                       (session['user_id'], product_id))
        
        mysql.connection.commit()
        flash('Product added to cart!', 'success')
    except Exception as e:
        flash('Error adding product to cart', 'error')
        print(e)  # For debugging
    finally:
        cur.close()
    
    return redirect(url_for('index'))

@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
@login_required
def remove_from_cart(product_id):
    cur = mysql.connection.cursor()
    try:
        cur.execute("DELETE FROM cart WHERE user_id = %s AND product_id = %s",
                   (session['user_id'], product_id))
        mysql.connection.commit()
        flash('Item removed from cart', 'success')
    except Exception as e:
        print(f"Remove from cart error: {e}")  # Debug print
        flash('Error removing item from cart', 'error')
    finally:
        cur.close()
    return redirect(url_for('cart'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('login'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM products")
    products = cur.fetchall()
    cur.close()
    return render_template('admin/dashboard.html', products=products)

@app.route('/admin/product/add', methods=['GET', 'POST'])
@admin_required
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        stock = request.form['stock']
        category = request.form['category']
        
        image = request.files['image']
        if image:
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], 'products', filename))
            image_url = f'products/{filename}'
        else:
            image_url = 'products/default.jpg'
        
        cur = mysql.connection.cursor()
        try:
            cur.execute("""
                INSERT INTO products (name, description, price, image_url, stock, category)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (name, description, price, image_url, stock, category))
            mysql.connection.commit()
            flash('Product added successfully!', 'success')
        except Exception as e:
            flash(f'Error adding product: {str(e)}', 'error')
        finally:
            cur.close()
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/add_product.html')

@app.route('/admin/product/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        stock = request.form['stock']
        category = request.form['category']
        
        try:
            if 'image' in request.files:
                image = request.files['image']
                if image.filename:
                    filename = secure_filename(image.filename)
                    image.save(os.path.join(app.config['UPLOAD_FOLDER'], 'products', filename))
                    image_url = f'products/{filename}'
                    
                    cur.execute("""
                        UPDATE products 
                        SET name=%s, description=%s, price=%s, image_url=%s, stock=%s, category=%s
                        WHERE id=%s
                    """, (name, description, price, image_url, stock, category, product_id))
                else:
                    cur.execute("""
                        UPDATE products 
                        SET name=%s, description=%s, price=%s, stock=%s, category=%s
                        WHERE id=%s
                    """, (name, description, price, stock, category, product_id))
            
            mysql.connection.commit()
            flash('Product updated successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            flash(f'Error updating product: {str(e)}', 'error')
        finally:
            cur.close()
    
    cur.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product = cur.fetchone()
    cur.close()
    
    return render_template('admin/edit_product.html', product=product)

@app.route('/admin/product/delete/<int:product_id>', methods=['POST'])
@admin_required
def delete_product(product_id):
    cur = mysql.connection.cursor()
    try:
        # First delete from cart to maintain referential integrity
        cur.execute("DELETE FROM cart WHERE product_id = %s", (product_id,))
        # Then delete the product
        cur.execute("DELETE FROM products WHERE id = %s", (product_id,))
        mysql.connection.commit()
        flash('Product deleted successfully!', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error deleting product: {str(e)}', 'error')
    finally:
        cur.close()
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
