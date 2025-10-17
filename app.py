from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, make_response
from flask_mysqldb import MySQL
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import MySQLdb.cursors
import re
import os
from datetime import datetime
import uuid
from email_templates import get_template, get_template_list

app = Flask(__name__)

# Configuration
from dotenv import load_dotenv
load_dotenv()

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', '6c8e6b5a7f29d34e8a2f47c19d7c4a913f8dbf63e2b5d7a4a8c1d94f2b7e6a9c')
# Disable template caching for development
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', '')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'ecommerce')

# Email configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', '587'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', '')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', '')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', app.config['MAIL_USERNAME'])

# File upload configuration
app.config['UPLOAD_FOLDER'] = 'static/images/products'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

mysql = MySQL(app)
mail = Mail(app)

# Cart Abandonment Detector Integration
from cart_abandonment_detector import CartAbandonmentDetector
import threading
import asyncio
import logging
import os

logger = logging.getLogger(__name__)

# Initialize Cart Abandonment Detector with Flask app context
cart_detector = CartAbandonmentDetector(mail_app=mail, flask_app=app)

def start_cart_detector():
    """Run cart abandonment detector in background thread"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(cart_detector.start_monitoring())
    except Exception as e:
        logger.error(f"Cart detector error: {e}")
    finally:
        loop.close()

# Start detector in background ONLY in main process (not in Flask reloader process)
# This prevents duplicate monitoring when debug mode is enabled
if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    detector_thread = threading.Thread(target=start_cart_detector, daemon=True)
    detector_thread.start()
    logger.info("Cart Abandonment Detector started in background")

# Helper function to check if user is logged in
def is_logged_in():
    return 'loggedin' in session

# Helper function to check if user is admin
def is_admin():
    return session.get('role') == 'admin'

@app.route('/')
def index():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM products WHERE stock > 0 ORDER BY created_at DESC LIMIT 12')
    products = cursor.fetchall()
    
    # Convert decimal prices to float
    for product in products:
        product['price'] = float(product['price'])
    
    cursor.close()
    return render_template('index.html', products=products)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()
        cursor.close()
        
        if user and check_password_hash(user['password'], password):
            session['loggedin'] = True
            session['id'] = user['id']
            session['email'] = user['email']
            session['name'] = user['name']
            session['role'] = user['role']
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password!', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        phone = request.form.get('phone', '')
        address = request.form.get('address', '')
        
        # Validation
        if not name or not email or not password:
            flash('Please fill in all required fields!', 'error')
            return render_template('register.html')
        
        if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            flash('Invalid email address!', 'error')
            return render_template('register.html')
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        account = cursor.fetchone()
        
        if account:
            flash('Account already exists!', 'error')
        else:
            hashed_password = generate_password_hash(password)
            cursor.execute('INSERT INTO users (name, email, password, phone, address) VALUES (%s, %s, %s, %s, %s)', 
                         (name, email, hashed_password, phone, address))
            mysql.connection.commit()
            flash('You have successfully registered!', 'success')
            return redirect(url_for('login'))
        
        cursor.close()
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('email', None)
    session.pop('name', None)
    session.pop('role', None)
    return redirect(url_for('index'))

@app.route('/products')
def products():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM products WHERE stock > 0')
    products = cursor.fetchall()
    
    # Convert decimal prices to float
    for product in products:
        product['price'] = float(product['price'])
    
    cursor.close()
    return render_template('products.html', products=products)

@app.route('/product/<int:id>')
def product_detail(id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM products WHERE id = %s', (id,))
    product = cursor.fetchone()
    cursor.close()
    
    if not product:
        flash('Product not found!', 'error')
        return redirect(url_for('products'))
    
    # Convert decimal price to float
    product['price'] = float(product['price'])
    
    return render_template('product_detail.html', product=product)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if not is_logged_in():
        return jsonify({'success': False, 'message': 'Please login first'})
    
    product_id = request.json.get('product_id')
    quantity = request.json.get('quantity', 1)
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Check if product exists and has enough stock
    cursor.execute('SELECT * FROM products WHERE id = %s', (product_id,))
    product = cursor.fetchone()
    
    if not product or product['stock'] < quantity:
        cursor.close()
        return jsonify({'success': False, 'message': 'Product not available'})
    
    # Check if item already in cart
    cursor.execute('SELECT * FROM cart WHERE user_id = %s AND product_id = %s', 
                   (session['id'], product_id))
    cart_item = cursor.fetchone()
    
    if cart_item:
        new_quantity = cart_item['quantity'] + quantity
        if new_quantity > product['stock']:
            cursor.close()
            return jsonify({'success': False, 'message': 'Not enough stock'})
        
        cursor.execute('UPDATE cart SET quantity = %s WHERE id = %s', 
                      (new_quantity, cart_item['id']))
    else:
        cursor.execute('INSERT INTO cart (user_id, product_id, quantity) VALUES (%s, %s, %s)', 
                      (session['id'], product_id, quantity))
    
    mysql.connection.commit()
    cursor.close()
    
    return jsonify({'success': True, 'message': 'Added to cart successfully'})

@app.route('/cart')
def cart():
    if not is_logged_in():
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    
    # Track email click if coming from abandonment email
    email_track_id = request.args.get('email_track')
    if email_track_id:
        try:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            # Update the cart_abandonment_log to track the click
            cursor.execute("""
                UPDATE cart_abandonment_log 
                SET link_clicked = TRUE, 
                    clicked_at = NOW(),
                    click_count = click_count + 1
                WHERE id = %s AND user_id = %s
            """, (email_track_id, session['id']))
            mysql.connection.commit()
            cursor.close()
            logger.info(f"Tracked email click: log_id={email_track_id}, user_id={session['id']}")
        except Exception as e:
            logger.error(f"Error tracking email click: {e}")
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('''
        SELECT c.*, p.name, p.price, p.image, (c.quantity * p.price) as total
        FROM cart c 
        JOIN products p ON c.product_id = p.id 
        WHERE c.user_id = %s
    ''', (session['id'],))
    cart_items = cursor.fetchall()
    
    # Convert decimal values to float to avoid template errors
    for item in cart_items:
        item['price'] = float(item['price'])
        item['total'] = float(item['total'])
    
    total_amount = float(sum(item['total'] for item in cart_items))
    cursor.close()
    
    return render_template('cart.html', cart_items=cart_items, total_amount=total_amount)

@app.route('/update_cart', methods=['POST'])
def update_cart():
    if not is_logged_in():
        return jsonify({'success': False, 'message': 'Please login first'})
    
    cart_id = request.json.get('cart_id')
    quantity = request.json.get('quantity')
    
    if quantity <= 0:
        return remove_from_cart()
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('UPDATE cart SET quantity = %s WHERE id = %s AND user_id = %s', 
                   (quantity, cart_id, session['id']))
    mysql.connection.commit()
    cursor.close()
    
    return jsonify({'success': True, 'message': 'Cart updated successfully'})

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    if not is_logged_in():
        return jsonify({'success': False, 'message': 'Please login first'})
    
    cart_id = request.json.get('cart_id')
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('DELETE FROM cart WHERE id = %s AND user_id = %s', (cart_id, session['id']))
    mysql.connection.commit()
    cursor.close()
    
    return jsonify({'success': True, 'message': 'Item removed from cart'})

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if not is_logged_in():
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('''
            SELECT c.*, p.name, p.price, p.stock, p.image, (c.quantity * p.price) as total
            FROM cart c 
            JOIN products p ON c.product_id = p.id 
            WHERE c.user_id = %s
        ''', (session['id'],))
        cart_items = cursor.fetchall()
        
        if not cart_items:
            flash('Your cart is empty!', 'error')
            return redirect(url_for('cart'))
        
        # Convert decimal values to float
        for item in cart_items:
            item['price'] = float(item['price'])
            item['total'] = float(item['total'])
        
        total_amount = float(sum(item['total'] for item in cart_items))
        
        if request.method == 'POST':
            # Create order
            order_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO orders (id, user_id, total_amount, status) 
                VALUES (%s, %s, %s, %s)
            ''', (order_id, session['id'], total_amount, 'pending'))
            
            # Add order items and update stock
            for item in cart_items:
                cursor.execute('''
                    INSERT INTO order_items (order_id, product_id, quantity, price) 
                    VALUES (%s, %s, %s, %s)
                ''', (order_id, item['product_id'], item['quantity'], item['price']))
                
                # Update stock
                cursor.execute('''
                    UPDATE products SET stock = stock - %s WHERE id = %s
                ''', (item['quantity'], item['product_id']))
            
            # Clear cart
            cursor.execute('DELETE FROM cart WHERE user_id = %s', (session['id'],))
            
            # Track conversion if user came from abandonment email
            cursor.execute("""
                UPDATE cart_abandonment_log 
                SET purchase_completed = TRUE,
                    completed_at = NOW()
                WHERE user_id = %s 
                AND email_sent = TRUE
                AND purchase_completed = FALSE
                AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                ORDER BY created_at DESC
                LIMIT 1
            """, (session['id'],))
            
            if cursor.rowcount > 0:
                logger.info(f"Tracked conversion for user {session['id']} from abandonment email")
            
            mysql.connection.commit()
            cursor.close()
            
            flash('Order placed successfully!', 'success')
            return redirect(url_for('order_success', order_id=order_id))
        
        cursor.close()
        return render_template('checkout.html', cart_items=cart_items, total_amount=total_amount)
        
    except Exception as e:
        app.logger.error(f"Checkout error: {str(e)}")
        # Return debug info
        return f"<h1>Checkout Debug Info</h1><p>Error: {str(e)}</p><p>User logged in: {is_logged_in()}</p><p>Session ID: {session.get('id', 'Not found')}</p>"

@app.route('/order_success/<order_id>')
def order_success(order_id):
    if not is_logged_in():
        return redirect(url_for('login'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM orders WHERE id = %s AND user_id = %s', (order_id, session['id']))
    order = cursor.fetchone()
    cursor.close()
    
    if not order:
        flash('Order not found!', 'error')
        return redirect(url_for('index'))
    
    return render_template('order_success.html', order=order)

@app.route('/track/email/<int:log_id>')
def track_email_open(log_id):
    """Track email opens with a 1x1 transparent pixel"""
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
            UPDATE cart_abandonment_log 
            SET email_opened = TRUE,
                opened_at = COALESCE(opened_at, NOW())
            WHERE id = %s AND email_opened = FALSE
        """, (log_id,))
        mysql.connection.commit()
        cursor.close()
        
        if cursor.rowcount > 0:
            logger.info(f"Tracked email open: log_id={log_id}")
        
        # Return a 1x1 transparent GIF pixel
        from io import BytesIO
        import base64
        
        # 1x1 transparent GIF
        gif_data = base64.b64decode('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7')
        
        response = make_response(gif_data)
        response.headers['Content-Type'] = 'image/gif'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
        
    except Exception as e:
        logger.error(f"Error tracking email open: {e}")
        # Still return the pixel even on error
        from io import BytesIO
        import base64
        gif_data = base64.b64decode('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7')
        response = make_response(gif_data)
        response.headers['Content-Type'] = 'image/gif'
        return response

@app.route('/orders')
def user_orders():
    if not is_logged_in():
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM orders WHERE user_id = %s ORDER BY created_at DESC', (session['id'],))
    orders = cursor.fetchall()
    cursor.close()
    
    return render_template('user_orders.html', orders=orders)

@app.route('/cancel_order/<order_id>', methods=['POST'])
def cancel_order(order_id):
    if not is_logged_in():
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Verify the order belongs to the user and is cancellable
        cursor.execute('''
            SELECT id, status FROM orders 
            WHERE id = %s AND user_id = %s
        ''', (order_id, session['id']))
        
        order = cursor.fetchone()
        
        if not order:
            cursor.close()
            return jsonify({'success': False, 'message': 'Order not found'}), 404
        
        # Only allow cancellation of pending or processing orders
        if order['status'] not in ['pending', 'processing']:
            cursor.close()
            return jsonify({'success': False, 'message': f'Cannot cancel order with status: {order["status"]}'}), 400
        
        # Update order status to cancelled
        cursor.execute('''
            UPDATE orders 
            SET status = 'cancelled'
            WHERE id = %s
        ''', (order_id,))
        
        mysql.connection.commit()
        cursor.close()
        
        logger.info(f"Order {order_id} cancelled by user {session['id']}")
        return jsonify({'success': True, 'message': 'Order cancelled successfully'})
        
    except Exception as e:
        logger.error(f"Error cancelling order: {e}")
        return jsonify({'success': False, 'message': 'An error occurred while cancelling the order'}), 500

# Admin routes
@app.route('/admin')
def admin_dashboard():
    if not is_logged_in():
        flash('Please login to access the admin panel', 'error')
        return redirect(url_for('login'))
    
    if not is_admin():
        flash('Access denied! Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    try:
        from datetime import datetime
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Get statistics with error handling
        cursor.execute('SELECT COUNT(*) as total_products FROM products')
        total_products = cursor.fetchone()['total_products']
        
        cursor.execute('SELECT COUNT(*) as total_users FROM users WHERE role = "user"')
        total_users = cursor.fetchone()['total_users']
        
        cursor.execute('SELECT COUNT(*) as total_orders FROM orders')
        total_orders = cursor.fetchone()['total_orders']
        
        cursor.execute('SELECT SUM(total_amount) as total_revenue FROM orders WHERE status = "completed"')
        total_revenue_result = cursor.fetchone()['total_revenue']
        total_revenue = float(total_revenue_result) if total_revenue_result else 0.0
        
        # Get abandoned carts count
        cursor.execute('''
            SELECT COUNT(DISTINCT user_id) as total_abandoned 
            FROM cart 
            WHERE TIMESTAMPDIFF(MINUTE, created_at, NOW()) >= 1
        ''')
        total_abandoned = cursor.fetchone()['total_abandoned']
        
        # Get recent orders
        cursor.execute('''
            SELECT o.*, u.name 
            FROM orders o 
            JOIN users u ON o.user_id = u.id 
            ORDER BY o.created_at DESC 
            LIMIT 5
        ''')
        recent_orders = cursor.fetchall()
        
        # Get low stock products
        cursor.execute('SELECT * FROM products WHERE stock < 10 ORDER BY stock ASC LIMIT 5')
        low_stock = cursor.fetchall()
        
        # Get detailed abandoned carts information
        cursor.execute('''
            SELECT 
                u.id as user_id,
                u.name,
                u.email,
                COUNT(c.id) as items_count,
                SUM(p.price * c.quantity) as cart_value,
                MIN(c.created_at) as first_added,
                MAX(c.created_at) as last_added,
                TIMESTAMPDIFF(MINUTE, MAX(c.created_at), NOW()) as minutes_ago
            FROM cart c
            JOIN users u ON c.user_id = u.id
            JOIN products p ON c.product_id = p.id
            WHERE TIMESTAMPDIFF(MINUTE, c.created_at, NOW()) >= 1
            GROUP BY u.id, u.name, u.email
            ORDER BY minutes_ago DESC
            LIMIT 20
        ''')
        abandoned_carts_raw = cursor.fetchall()
        
        # Get recent abandonment emails from cart_abandonment_log
        cursor.execute('''
            SELECT 
                cal.id,
                u.email,
                cal.cart_total as cart_value,
                cal.created_at as sent_at,
                15 as discount_offered,
                cal.email_opened as opened,
                cal.link_clicked as clicked,
                cal.purchase_completed as converted,
                cal.click_count,
                cal.opened_at,
                cal.clicked_at,
                cal.completed_at
            FROM cart_abandonment_log cal
            JOIN users u ON cal.user_id = u.id
            WHERE cal.email_sent = TRUE
            ORDER BY cal.created_at DESC
            LIMIT 10
        ''')
        recent_emails = cursor.fetchall()
        
        # Process abandoned carts data to split name into first and last
        abandoned_carts = []
        for cart in abandoned_carts_raw:
            name_parts = cart['name'].split(' ', 1)
            abandoned_carts.append({
                'user_id': cart['user_id'],
                'first_name': name_parts[0],
                'last_name': name_parts[1] if len(name_parts) > 1 else '',
                'email': cart['email'],
                'items_count': cart['items_count'],
                'cart_value': float(cart['cart_value']) if cart['cart_value'] else 0.0,
                'minutes_ago': cart['minutes_ago']
            })
        
        cursor.close()
        
        # Format current date
        current_date = datetime.now().strftime('%B %d, %Y')
        
        return render_template('admin/dashboard.html', 
                             total_products=total_products,
                             total_users=total_users,
                             total_orders=total_orders,
                             total_revenue=total_revenue,
                             total_abandoned=total_abandoned,
                             current_date=current_date,
                             recent_orders=recent_orders,
                             low_stock=low_stock,
                             abandoned_carts=abandoned_carts,
                             recent_emails=recent_emails)
    except Exception as e:
        app.logger.error(f"Admin dashboard error: {str(e)}")
        flash(f'Error loading admin dashboard: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/admin/products')
def admin_products():
    if not is_logged_in() or not is_admin():
        flash('Access denied!', 'error')
        return redirect(url_for('index'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM products ORDER BY created_at DESC')
    products = cursor.fetchall()
    
    # Convert decimal prices to float
    for product in products:
        if product['price']:
            product['price'] = float(product['price'])
    
    cursor.close()
    
    return render_template('admin/products.html', products=products, timestamp=datetime.now())

@app.route('/admin/view_product/<int:product_id>')
def admin_view_product(product_id):
    app.logger.info(f"View product route accessed for product ID: {product_id}")
    
    if not is_logged_in() or not is_admin():
        app.logger.warning(f"Access denied for view product {product_id}")
        flash('Access denied!', 'error')
        return redirect(url_for('index'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM products WHERE id = %s', (product_id,))
    product = cursor.fetchone()
    cursor.close()
    
    if not product:
        flash('Product not found!', 'error')
        return redirect(url_for('admin_products'))
    
    # Convert decimal price to float
    if product['price']:
        product['price'] = float(product['price'])
    
    return render_template('admin/view_product.html', product=product)

@app.route('/admin/edit_product/<int:product_id>', methods=['GET', 'POST'])
def admin_edit_product(product_id):
    app.logger.info(f"Edit product route accessed for product ID: {product_id}, method: {request.method}")
    
    if not is_logged_in() or not is_admin():
        app.logger.warning(f"Access denied for edit product {product_id}")
        flash('Access denied!', 'error')
        return redirect(url_for('index'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    if request.method == 'POST':
        # Update product
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        stock = int(request.form['stock'])
        category = request.form['category']
        
        try:
            cursor.execute('''
                UPDATE products 
                SET name = %s, description = %s, price = %s, stock = %s, category = %s
                WHERE id = %s
            ''', (name, description, price, stock, category, product_id))
            
            mysql.connection.commit()
            cursor.close()
            
            flash('Product updated successfully!', 'success')
            return redirect(url_for('admin_products'))
            
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            flash(f'Error updating product: {str(e)}', 'error')
            return redirect(url_for('admin_edit_product', product_id=product_id))
    
    # GET request - show edit form
    cursor.execute('SELECT * FROM products WHERE id = %s', (product_id,))
    product = cursor.fetchone()
    cursor.close()
    
    if not product:
        flash('Product not found!', 'error')
        return redirect(url_for('admin_products'))
    
    # Convert decimal prices to float
    if product['price']:
        product['price'] = float(product['price'])
    
    return render_template('admin/edit_product.html', product=product)

@app.route('/admin/delete_product/<int:product_id>', methods=['DELETE', 'POST'])
def admin_delete_product(product_id):
    app.logger.info(f"Delete product request for ID: {product_id}, Method: {request.method}")
    
    if not is_logged_in() or not is_admin():
        app.logger.error(f"Access denied for delete product {product_id}")
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Check if product exists
        cursor.execute('SELECT * FROM products WHERE id = %s', (product_id,))
        product = cursor.fetchone()
        
        if not product:
            cursor.close()
            app.logger.error(f"Product {product_id} not found")
            return jsonify({'success': False, 'message': 'Product not found'}), 404
        
        app.logger.info(f"Found product: {product['name']}")
        
        # Check if product is in any orders (prevent deletion if it has order history)
        cursor.execute('SELECT COUNT(*) as count FROM order_items WHERE product_id = %s', (product_id,))
        order_count = cursor.fetchone()['count']
        
        if order_count > 0:
            cursor.close()
            app.logger.warning(f"Cannot delete product {product_id} - has {order_count} orders")
            return jsonify({'success': False, 'message': f'Cannot delete product with existing orders ({order_count} orders found). This product is part of order history.'}), 400
        
        # Check if product is in any carts
        cursor.execute('SELECT COUNT(*) as count FROM cart WHERE product_id = %s', (product_id,))
        cart_count = cursor.fetchone()['count']
        
        # Remove from carts if present
        if cart_count > 0:
            app.logger.info(f"Removing product {product_id} from {cart_count} carts")
            cursor.execute('DELETE FROM cart WHERE product_id = %s', (product_id,))
        
        # Delete the product
        app.logger.info(f"Deleting product {product_id}")
        cursor.execute('DELETE FROM products WHERE id = %s', (product_id,))
        
        mysql.connection.commit()
        cursor.close()
        
        app.logger.info(f"Successfully deleted product {product_id}")
        return jsonify({'success': True, 'message': 'Product deleted successfully'})
        
    except Exception as e:
        app.logger.error(f"Error deleting product {product_id}: {str(e)}")
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500

@app.route('/test-delete/<int:product_id>')
def test_delete(product_id):
    """Test route to verify delete endpoint is accessible"""
    return f"<h1>Test Delete Route</h1><p>Product ID: {product_id}</p><p>Logged in: {is_logged_in()}</p><p>Is admin: {is_admin() if is_logged_in() else 'N/A'}</p>"

@app.route('/test-admin-routes')
def test_admin_routes():
    """Test route to verify all admin routes are working"""
    try:
        routes = [
            ('Dashboard', url_for('admin_dashboard')),
            ('Products', url_for('admin_products')),
            ('Orders', url_for('admin_orders')),
            ('Customers', url_for('admin_customers')),
            ('Reports', url_for('admin_reports')),
            ('Settings', url_for('admin_settings')),
        ]
        
        html = "<h1>Admin Routes Test</h1>"
        html += f"<p>Logged in: {is_logged_in()}</p>"
        html += f"<p>Is admin: {is_admin() if is_logged_in() else 'N/A'}</p>"
        html += "<h3>Available Routes:</h3><ul>"
        
        for name, url in routes:
            html += f'<li><a href="{url}" target="_blank">{name}</a> - {url}</li>'
        
        html += "</ul>"
        
        # Test if routes actually work
        html += "<h3>Direct Route Tests:</h3><ul>"
        html += f'<li><a href="/admin/customers">Direct Customers Link</a></li>'
        html += f'<li><a href="/admin/reports">Direct Reports Link</a></li>'
        html += f'<li><a href="/admin/settings">Direct Settings Link</a></li>'
        html += "</ul>"
        
        return html
        
    except Exception as e:
        return f"<h1>Error in route generation</h1><p>{str(e)}</p>"

@app.route('/debug-routes')
def debug_routes():
    """Show all registered Flask routes"""
    html = "<h1>All Registered Flask Routes</h1><ul>"
    
    for rule in app.url_map.iter_rules():
        methods = ', '.join(rule.methods - {'HEAD', 'OPTIONS'})
        html += f'<li><strong>{rule.endpoint}</strong>: {rule.rule} [{methods}]</li>'
    
    html += "</ul>"
    
    # Test specific routes
    html += "<h2>Direct Route Tests</h2><ul>"
    html += f'<li><a href="/admin/view_product/1">Test View Product 1</a></li>'
    html += f'<li><a href="/admin/edit_product/1">Test Edit Product 1</a></li>'
    html += f'<li><a href="/admin/products">Back to Products</a></li>'
    html += "</ul>"
    
    return html

@app.route('/admin/add_product', methods=['GET', 'POST'])
def admin_add_product():
    if not is_logged_in() or not is_admin():
        flash('Access denied!', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        stock = int(request.form['stock'])
        category = request.form['category']
        
        # Handle file upload
        image_filename = 'default.jpg'
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                filename = secure_filename(file.filename)
                image_filename = str(uuid.uuid4()) + '_' + filename
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
        
        cursor = mysql.connection.cursor()
        cursor.execute('''
            INSERT INTO products (name, description, price, stock, category, image) 
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (name, description, price, stock, category, image_filename))
        mysql.connection.commit()
        cursor.close()
        
        flash('Product added successfully!', 'success')
        return redirect(url_for('admin_products'))
    
    return render_template('admin/add_product.html')

@app.route('/admin/orders')
def admin_orders():
    if not is_logged_in() or not is_admin():
        flash('Access denied!', 'error')
        return redirect(url_for('index'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('''
        SELECT o.*, u.name as user_name, u.email 
        FROM orders o 
        JOIN users u ON o.user_id = u.id 
        WHERE o.status != 'cancelled'
        ORDER BY o.created_at DESC
    ''')
    orders = cursor.fetchall()
    cursor.close()
    
    return render_template('admin/orders.html', orders=orders)

@app.route('/admin/update_order_status', methods=['POST'])
def update_order_status():
    if not is_logged_in() or not is_admin():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        order_id = data.get('order_id')
        status = data.get('status')
        
        if not order_id or not status:
            return jsonify({'success': False, 'message': 'Missing order ID or status'}), 400
        
        # Valid status values
        valid_statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
        if status not in valid_statuses:
            return jsonify({'success': False, 'message': 'Invalid status'}), 400
        
        cursor = mysql.connection.cursor()
        cursor.execute('''
            UPDATE orders 
            SET status = %s, updated_at = NOW() 
            WHERE id = %s
        ''', (status, order_id))
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({'success': True, 'message': 'Order status updated successfully'})
        
    except Exception as e:
        app.logger.error(f"Error updating order status: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.route('/admin/order_details/<order_id>')
def order_details(order_id):
    if not is_logged_in() or not is_admin():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Get order details
        cursor.execute('''
            SELECT o.*, u.name as user_name, u.email, u.phone, u.address
            FROM orders o 
            JOIN users u ON o.user_id = u.id 
            WHERE o.id = %s
        ''', (order_id,))
        order = cursor.fetchone()
        
        if not order:
            return jsonify({'success': False, 'message': 'Order not found'}), 404
        
        # Get order items
        cursor.execute('''
            SELECT oi.*, p.name as product_name, p.image 
            FROM order_items oi 
            JOIN products p ON oi.product_id = p.id 
            WHERE oi.order_id = %s
        ''', (order_id,))
        order_items = cursor.fetchall()
        cursor.close()
        
        # Generate HTML for order details
        html = f'''
        <div class="row">
            <div class="col-md-6">
                <h6>Order Information</h6>
                <p><strong>Order ID:</strong> #{order['id']}</p>
                <p><strong>Date:</strong> {order['created_at'].strftime('%Y-%m-%d %H:%M')}</p>
                <p><strong>Status:</strong> 
                    <span class="badge bg-info">{order['status'].title()}</span>
                </p>
                <p><strong>Payment Status:</strong> 
                    <span class="badge bg-{'success' if order['payment_status'] == 'completed' else 'warning'}">
                        {order['payment_status'].title() if order['payment_status'] else 'Pending'}
                    </span>
                </p>
                <p><strong>Total Amount:</strong> ${float(order['total_amount']):.2f}</p>
            </div>
            <div class="col-md-6">
                <h6>Customer Information</h6>
                <p><strong>Name:</strong> {order['user_name']}</p>
                <p><strong>Email:</strong> {order['email']}</p>
                <p><strong>Phone:</strong> {order['phone'] if order['phone'] else 'N/A'}</p>
                <p><strong>Address:</strong> {order['address'] if order['address'] else 'N/A'}</p>
            </div>
        </div>
        <hr>
        <h6>Order Items</h6>
        <div class="table-responsive">
            <table class="table table-sm">
                <thead>
                    <tr>
                        <th>Product</th>
                        <th>Quantity</th>
                        <th>Price</th>
                        <th>Total</th>
                    </tr>
                </thead>
                <tbody>
        '''
        
        for item in order_items:
            html += f'''
                    <tr>
                        <td>{item['product_name']}</td>
                        <td>{item['quantity']}</td>
                        <td>${float(item['price']):.2f}</td>
                        <td>${float(item['quantity']) * float(item['price']):.2f}</td>
                    </tr>
            '''
        
        html += '''
                </tbody>
            </table>
        </div>
        '''
        
        return jsonify({'success': True, 'html': html})
        
    except Exception as e:
        app.logger.error(f"Error fetching order details: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.route('/admin/print_order/<order_id>')
def print_order(order_id):
    if not is_logged_in() or not is_admin():
        flash('Access denied!', 'error')
        return redirect(url_for('index'))
    
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Get order details
        cursor.execute('''
            SELECT o.*, u.name as user_name, u.email, u.phone, u.address
            FROM orders o 
            JOIN users u ON o.user_id = u.id 
            WHERE o.id = %s
        ''', (order_id,))
        order = cursor.fetchone()
        
        if not order:
            flash('Order not found!', 'error')
            return redirect(url_for('admin_orders'))
        
        # Get order items
        cursor.execute('''
            SELECT oi.*, p.name as product_name 
            FROM order_items oi 
            JOIN products p ON oi.product_id = p.id 
            WHERE oi.order_id = %s
        ''', (order_id,))
        order_items = cursor.fetchall()
        cursor.close()
        
        return render_template('admin/print_order.html', order=order, order_items=order_items)
        
    except Exception as e:
        app.logger.error(f"Error preparing order for printing: {e}")
        flash('Error loading order for printing!', 'error')
        return redirect(url_for('admin_orders'))

@app.route('/admin/export_orders')
def export_orders():
    if not is_logged_in() or not is_admin():
        flash('Access denied!', 'error')
        return redirect(url_for('index'))
    
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('''
            SELECT o.id, o.created_at, o.status, o.payment_status, o.total_amount,
                   u.name as user_name, u.email
            FROM orders o 
            JOIN users u ON o.user_id = u.id 
            ORDER BY o.created_at DESC
        ''')
        orders = cursor.fetchall()
        cursor.close()
        
        # Generate CSV content
        import csv
        import io
        from flask import make_response
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Order ID', 'Date', 'Customer Name', 'Email', 'Status', 'Payment Status', 'Total Amount'])
        
        # Write data
        for order in orders:
            writer.writerow([
                order['id'],
                order['created_at'].strftime('%Y-%m-%d %H:%M'),
                order['user_name'],
                order['email'],
                order['status'],
                order['payment_status'],
                f"${float(order['total_amount']):.2f}"
            ])
        
        output.seek(0)
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename=orders_export.csv'
        
        return response
        
    except Exception as e:
        app.logger.error(f"Error exporting orders: {e}")
        flash('Error exporting orders!', 'error')
        return redirect(url_for('admin_orders'))

@app.route('/admin/customers')
def admin_customers():
    app.logger.info("Admin customers route accessed")
    
    if not is_logged_in() or not is_admin():
        app.logger.warning("Access denied to admin customers")
        flash('Access denied!', 'error')
        return redirect(url_for('index'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('''
        SELECT u.*, 
               COUNT(DISTINCT o.id) as total_orders,
               COALESCE(SUM(o.total_amount), 0) as total_spent
        FROM users u 
        LEFT JOIN orders o ON u.id = o.user_id 
        WHERE u.role = "user"
        GROUP BY u.id 
        ORDER BY u.created_at DESC
    ''')
    customers = cursor.fetchall()
    
    # Convert decimal values to float
    for customer in customers:
        if customer['total_spent']:
            customer['total_spent'] = float(customer['total_spent'])
    
    cursor.close()
    
    return render_template('admin/customers.html', customers=customers)

@app.route('/admin/customer_details/<customer_id>')
def customer_details(customer_id):
    app.logger.info(f"Customer details route accessed for ID: {customer_id}")
    
    if not is_logged_in() or not is_admin():
        app.logger.warning("Access denied to customer details")
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Get customer details
        cursor.execute('''
            SELECT u.*, 
                   COUNT(DISTINCT o.id) as total_orders,
                   COALESCE(SUM(o.total_amount), 0) as total_spent
            FROM users u 
            LEFT JOIN orders o ON u.id = o.user_id 
            WHERE u.id = %s AND u.role = "user"
            GROUP BY u.id
        ''', (customer_id,))
        customer = cursor.fetchone()
        
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        
        # Get recent orders
        cursor.execute('''
            SELECT o.*, 
                   DATE_FORMAT(o.created_at, '%%Y-%%m-%%d %%H:%%i') as formatted_date
            FROM orders o 
            WHERE o.user_id = %s 
            ORDER BY o.created_at DESC 
            LIMIT 10
        ''', (customer_id,))
        recent_orders = cursor.fetchall()
        
        # Get user address from user table
        cursor.execute('''
            SELECT address 
            FROM users 
            WHERE id = %s AND address IS NOT NULL
        ''', (customer_id,))
        address_result = cursor.fetchone()
        addresses = [{'address': address_result['address']}] if address_result and address_result['address'] else []
        
        cursor.close()
        
        # Convert decimal values
        if customer['total_spent']:
            customer['total_spent'] = float(customer['total_spent'])
        
        for order in recent_orders:
            if order['total_amount']:
                order['total_amount'] = float(order['total_amount'])
        
        return jsonify({
            'customer': customer,
            'recent_orders': recent_orders,
            'addresses': addresses
        })
        
    except Exception as e:
        app.logger.error(f"Error fetching customer details: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/admin/send_customer_email', methods=['POST'])
def send_customer_email():
    app.logger.info("Send customer email route accessed")
    
    if not is_logged_in() or not is_admin():
        app.logger.warning("Access denied to send customer email")
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        customer_id = data.get('customer_id')
        customer_email = data.get('customer_email')
        subject = data.get('subject')
        message_body = data.get('message')
        
        # Validate required fields
        if not all([customer_id, customer_email, subject, message_body]):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        # Check if email is configured
        if not app.config.get('MAIL_USERNAME') or not app.config.get('MAIL_PASSWORD'):
            app.logger.warning("Email not configured - simulating email send")
            return jsonify({
                'success': True, 
                'message': f'Email simulated (not configured): {subject} to {customer_email}',
                'simulated': True
            })
        
        try:
            # Create and send actual email
            msg = Message(
                subject=subject,
                recipients=[customer_email],
                body=message_body,
                sender=app.config['MAIL_DEFAULT_SENDER']
            )
            
            # Add HTML version for better formatting
            msg.html = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <div style="background-color: #007bff; color: white; padding: 20px; text-align: center;">
                            <h2>E-Commerce Store</h2>
                        </div>
                        <div style="padding: 20px; background-color: #f8f9fa;">
                            <p>Dear Valued Customer,</p>
                            <div style="background-color: white; padding: 20px; border-left: 4px solid #007bff;">
                                {message_body.replace(chr(10), '<br>')}
                            </div>
                            <p style="margin-top: 20px;">
                                Best regards,<br>
                                <strong>E-Commerce Store Team</strong>
                            </p>
                        </div>
                        <div style="text-align: center; padding: 20px; color: #666; font-size: 12px;">
                            <p>This email was sent from our admin panel. Please do not reply directly to this email.</p>
                        </div>
                    </div>
                </body>
            </html>
            """
            
            mail.send(msg)
            app.logger.info(f"Email successfully sent to {customer_email} with subject: {subject}")
            
            return jsonify({
                'success': True, 
                'message': f'Email sent successfully to {customer_email}!'
            })
            
        except Exception as email_error:
            app.logger.error(f"Error sending email: {str(email_error)}")
            return jsonify({
                'success': False, 
                'message': f'Failed to send email: {str(email_error)}'
            }), 500
        
    except Exception as e:
        app.logger.error(f"Error processing customer email request: {str(e)}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.route('/admin/email_templates')
def get_email_templates():
    if not is_logged_in() or not is_admin():
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        templates = get_template_list()
        return jsonify({'success': True, 'templates': templates})
    except Exception as e:
        app.logger.error(f"Error fetching email templates: {str(e)}")
        return jsonify({'success': False, 'message': 'Error fetching templates'}), 500

@app.route('/admin/email_template/<template_name>')
def get_email_template(template_name):
    if not is_logged_in() or not is_admin():
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        template = get_template(template_name)
        return jsonify({'success': True, 'template': template})
    except Exception as e:
        app.logger.error(f"Error fetching email template {template_name}: {str(e)}")
        return jsonify({'success': False, 'message': 'Error fetching template'}), 500

@app.route('/admin/reports')
def admin_reports():
    if not is_logged_in() or not is_admin():
        flash('Access denied!', 'error')
        return redirect(url_for('index'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Sales statistics
    cursor.execute('''
        SELECT 
            COUNT(*) as total_orders,
            SUM(total_amount) as total_revenue,
            AVG(total_amount) as avg_order_value,
            DATE(created_at) as order_date
        FROM orders 
        WHERE status = "completed"
        GROUP BY DATE(created_at)
        ORDER BY order_date DESC
        LIMIT 30
    ''')
    daily_sales = cursor.fetchall()
    
    # Top selling products
    cursor.execute('''
        SELECT p.name, p.price, SUM(oi.quantity) as total_sold,
               SUM(oi.quantity * oi.price) as revenue
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        JOIN orders o ON oi.order_id = o.id
        WHERE o.status = "completed"
        GROUP BY p.id, p.name, p.price
        ORDER BY total_sold DESC
        LIMIT 10
    ''')
    top_products = cursor.fetchall()
    
    # Convert decimal values to float
    for sale in daily_sales:
        if sale['total_revenue']:
            sale['total_revenue'] = float(sale['total_revenue'])
        if sale['avg_order_value']:
            sale['avg_order_value'] = float(sale['avg_order_value'])
    
    for product in top_products:
        if product['price']:
            product['price'] = float(product['price'])
        if product['revenue']:
            product['revenue'] = float(product['revenue'])
    
    cursor.close()
    
    # Format current date
    from datetime import datetime
    current_date = datetime.now().strftime('%B %d, %Y')
    
    return render_template('admin/reports.html', 
                         daily_sales=daily_sales, 
                         top_products=top_products,
                         current_date=current_date)

@app.route('/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    if not is_logged_in() or not is_admin():
        flash('Access denied!', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Handle settings updates
        action = request.form.get('action')
        
        if action == 'update_site_settings':
            # This would typically update site configuration
            flash('Site settings updated successfully!', 'success')
        elif action == 'backup_database':
            # This would typically trigger a database backup
            flash('Database backup initiated!', 'success')
        elif action == 'clear_cache':
            # This would typically clear application cache
            flash('Cache cleared successfully!', 'success')
    
    # Get some basic statistics for settings page
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    cursor.execute('SELECT COUNT(*) as count FROM products')
    product_count = cursor.fetchone()['count']
    
    cursor.execute('SELECT COUNT(*) as count FROM users WHERE role = "user"')
    customer_count = cursor.fetchone()['count']
    
    cursor.execute('SELECT COUNT(*) as count FROM orders')
    order_count = cursor.fetchone()['count']
    
    cursor.close()
    
    stats = {
        'products': product_count,
        'customers': customer_count,
        'orders': order_count
    }
    
    return render_template('admin/settings.html', stats=stats)

@app.route('/test-images')
def test_images():
    """Test route to check if images are accessible"""
    import os
    
    static_dir = os.path.join(app.root_path, 'static')
    images_dir = os.path.join(static_dir, 'images', 'products')
    
    result = {
        'static_dir_exists': os.path.exists(static_dir),
        'images_dir_exists': os.path.exists(images_dir),
        'product_images': [],
        'static_url_path': app.static_url_path,
        'static_folder': app.static_folder
    }
    
    if os.path.exists(images_dir):
        result['product_images'] = os.listdir(images_dir)
    
    # Get sample product from database
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT name, image FROM products LIMIT 1')
    sample_product = cursor.fetchone()
    cursor.close()
    
    if sample_product:
        result['sample_product'] = sample_product
        result['sample_image_path'] = url_for('static', filename=f"images/products/{sample_product['image']}")
    
    return f"<pre>{str(result)}</pre>"

if __name__ == '__main__':
    # Development configuration for template debugging
    app.config['DEBUG'] = True
    app.config['ENV'] = 'development'
    app.run(host='127.0.0.1', port=8080, debug=True)  # Only localhost access