# E-Commerce Platform

A comprehensive e-commerce web application built with Flask (Python) and MySQL database.

## Features

- **User Authentication**: Registration, login, logout with secure password hashing
- **Product Catalog**: Browse products with categories, search, and filtering
- **Shopping Cart**: Add/remove items, update quantities, persistent cart
- **Checkout System**: Complete order processing with payment simulation
- **Order Management**: Track orders, order history
- **Admin Panel**: Product management, order management, dashboard analytics
- **Responsive Design**: Mobile-friendly Bootstrap interface
- **Security**: Input validation, SQL injection prevention, CSRF protection

## Technologies Used

- **Backend**: Flask (Python web framework)
- **Database**: MySQL
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Authentication**: Werkzeug password hashing
- **File Upload**: Secure image handling for products

## Installation & Setup

### Prerequisites

1. **Python 3.8+** installed on your system
2. **MySQL Server** installed and running
3. **pip** (Python package installer)

### Database Setup

1. Start your MySQL server
2. Create the database and tables:

```sql
-- Run the contents of database.sql file in MySQL
mysql -u root -p < database.sql
```

Or manually execute the SQL commands in `database.sql`

### Application Setup

1. **Clone/Download the project**
   ```bash
   cd ecom
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure database connection**:
   Edit the database configuration in `app.py`:
   ```python
   app.config['MYSQL_HOST'] = 'localhost'
   app.config['MYSQL_USER'] = 'root'          # Your MySQL username
   app.config['MYSQL_PASSWORD'] = 'password'  # Your MySQL password
   app.config['MYSQL_DB'] = 'ecommerce'
   ```

5. **Create required directories**:
   ```bash
   mkdir -p static/images/products
   ```

6. **Add sample product images** (optional):
   Place product images in `static/images/products/` directory

7. **Run the application**:
   ```bash
   python app.py
   ```

8. **Access the application**:
   Open your web browser and go to: `http://127.0.0.1:5000`

## Default Login Credentials

### Admin Account
- **Email**: admin@ecommerce.com
- **Password**: admin123

### Creating User Accounts
Users can register new accounts through the registration page.

## Project Structure

```
ecom/
├── app.py                  # Main Flask application
├── database.sql            # Database schema and sample data
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── static/                # Static files
│   ├── css/
│   │   └── style.css      # Custom styles
│   ├── js/
│   │   └── main.js        # JavaScript functionality
│   └── images/            # Image assets
│       └── products/      # Product images
└── templates/             # HTML templates
    ├── base.html          # Base template
    ├── index.html         # Homepage
    ├── login.html         # Login page
    ├── register.html      # Registration page
    ├── products.html      # Product listing
    ├── cart.html          # Shopping cart
    ├── checkout.html      # Checkout page
    └── admin/             # Admin templates
        └── dashboard.html # Admin dashboard
```

## Key Features Explained

### User Management
- Secure user registration and authentication
- Password hashing using Werkzeug
- Session management for logged-in users
- Role-based access (user/admin)

### Product Catalog
- Product listing with pagination
- Category-based filtering
- Price range filtering
- Search functionality
- Product detail pages

### Shopping Cart
- Add products to cart
- Update quantities
- Remove items
- Cart persistence across sessions
- Real-time total calculation

### Order Processing
- Secure checkout process
- Order confirmation
- Order history tracking
- Admin order management

### Admin Panel
- Product CRUD operations
- Order management
- Dashboard with statistics
- User management capabilities

## API Endpoints

### Public Endpoints
- `GET /` - Homepage
- `GET /products` - Product listing
- `GET /product/<id>` - Product details
- `POST /login` - User login
- `POST /register` - User registration

### Protected Endpoints (Require Login)
- `GET /cart` - View cart
- `POST /add_to_cart` - Add item to cart
- `POST /checkout` - Process order
- `GET /orders` - User's order history

### Admin Endpoints (Require Admin Role)
- `GET /admin` - Admin dashboard
- `GET /admin/products` - Manage products
- `POST /admin/add_product` - Add new product
- `GET /admin/orders` - Manage orders

## Security Features

- Password hashing with Werkzeug
- SQL injection prevention using parameterized queries
- Input validation and sanitization
- File upload security for product images
- Session management
- CSRF protection (can be enhanced)

## Customization

### Adding New Product Categories
1. Update the categories table in the database
2. Modify the category filter in `products.html`
3. Update the admin product form

### Styling Changes
- Modify `static/css/style.css` for custom styles
- Bootstrap classes can be customized
- Update templates for layout changes

### Payment Integration
The current implementation simulates payment processing. To integrate real payment gateways:
1. Choose a payment provider (Stripe, PayPal, etc.)
2. Add their SDK to requirements.txt
3. Implement payment processing in the checkout route
4. Update checkout.html with payment forms

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Verify MySQL server is running
   - Check database credentials in app.py
   - Ensure database 'ecommerce' exists

2. **Import Error for MySQLdb**
   - On Windows: `pip install mysqlclient`
   - On macOS: `brew install mysql` then `pip install mysqlclient`
   - Alternative: Use PyMySQL instead

3. **File Upload Issues**
   - Ensure static/images/products directory exists
   - Check file permissions
   - Verify upload folder configuration

4. **Port Already in Use**
   - Change port in app.py: `app.run(debug=True, port=5001)`
   - Or stop other Flask applications

### Performance Optimization

1. **Database Indexing**
   - Add indexes on frequently queried columns
   - Optimize SQL queries

2. **Image Optimization**
   - Compress product images
   - Use appropriate image formats
   - Implement lazy loading

3. **Caching**
   - Add Flask-Caching for database queries
   - Cache static files with proper headers

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the code comments
3. Create an issue in the repository

---

**Note**: This is a demonstration e-commerce platform. For production use, additional security measures, payment integration, and performance optimizations should be implemented.