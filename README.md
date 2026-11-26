# Shopping Cart Recovery AI — E-Commerce Platform with Smart Abandoned-Cart Emails

A full e-commerce web application built with **Flask** and **MySQL**, plus an **AI-powered cart abandonment detector**. When a signed-in customer leaves items in their cart and goes idle, the system notices, writes a personalised recovery email with an LLM (Groq · Llama 3.3 70B), adds product recommendations and a discount based on the cart value, sends it, and tracks whether the email was opened.

---

## Table of contents

1. [Features](#features)
2. [How cart recovery works](#how-cart-recovery-works)
3. [Tech stack](#tech-stack)
4. [Project structure](#project-structure)
5. [Prerequisites](#prerequisites)
6. [Run locally](#run-locally)
7. [Environment variables](#environment-variables)
8. [Database schema](#database-schema)
9. [Admin account](#admin-account)
10. [Routes](#routes)
11. [Tuning the detector](#tuning-the-detector)
12. [Production server](#production-server)
13. [Troubleshooting](#troubleshooting)
14. [More documentation](#more-documentation)

---

## Features

**Store (customers)**

- Register, log in, log out (Werkzeug password hashing); profile page and account deletion
- Product catalogue with categories, search and product detail pages
- Shopping cart — add, update quantity, remove; live cart count badge
- Checkout that creates an order and reduces stock
- Order history and order cancellation

**Admin panel** (`/admin`)

- Dashboard with sales and order statistics
- Products — add (with image upload), view, edit, delete
- Orders — list, view details, update status, print, export
- Customers — list, view details, send an email from ready-made templates
- Reports and store settings

**AI cart recovery**

- Background detector checks carts every 30 seconds
- A cart counts as abandoned after a period of inactivity (1 minute by default, for demos)
- Recovery email written by an LLM via the Groq API, personalised with the customer's name and cart
- **Recommendations** of related products using TF-IDF / cosine similarity (scikit-learn) with stemming (NLTK)
- **Tiered discounts** — 10% for carts over $100, 20% over $500
- **Open tracking** — a tracking pixel records when the email is opened (`/track/email/<id>`)
- Duplicate protection — the same cart doesn't get emailed twice
- Every email is logged in `cart_abandonment_log`

## How cart recovery works

```
Customer adds items ──► users.last_activity updated on each request
                               │
Detector thread (every 30 s) ──┤ finds carts idle longer than ABANDONMENT_THRESHOLD_MINUTES
                               ▼
              cart hash already emailed? ── yes ──► skip
                               │ no
                               ▼
       recommend similar products (TF-IDF + cosine similarity)
       pick discount tier from cart total
       LLM writes subject + personalised body (Groq, Llama 3.3 70B)
                               ▼
       send HTML email (SMTP / Flask-Mail) with tracking pixel
                               ▼
       log in cart_abandonment_log  ──►  opened? → email_opened, opened_at
```

The detector starts automatically with the Flask app (one background thread), and can also run on its own with `cart_abandonment_detector/run_detector.py`.

## Tech stack

| Part | Technology |
|---|---|
| Backend | Python 3, Flask 2.3, Flask-MySQLdb, Flask-Mail |
| Database | MySQL 8 |
| Frontend | Jinja2 templates, HTML5, CSS3, JavaScript, Bootstrap 5 |
| AI text | Groq API (OpenAI-compatible client), model `llama-3.3-70b-versatile` |
| Recommendations | scikit-learn, NumPy, NLTK (Porter stemmer) |
| Images | Pillow |
| Production | Waitress (Windows) or Gunicorn (Linux) |

## Project structure

```
Shopping_Cart_Recovery_AI_Project/
├── app.py                        # Flask app: store, cart, checkout, admin, email tracking (port 8080)
├── config.py                     # Config classes (dev / production)
├── email_templates.py            # Admin email templates
├── wsgi.py, production_server.py # Production entry points (Waitress)
├── start.bat, start_production.bat
├── requirements.txt
├── .env.production               # Example production settings
├── templates/                    # Store pages + templates/admin/*
├── static/                       # css/style.css, js/main.js, images/products/
├── cart_abandonment_detector/
│   ├── cart_abandonment_detector.py   # Detection, recommendations, LLM email, sending, logging
│   ├── config.py                      # Thresholds, discount tiers, Groq model, DB, BASE_URL
│   ├── run_detector.py                # Run the detector on its own
│   ├── integration_example.py
│   └── *.md                           # Architecture, quick start, test reports
├── migrations/                   # add_last_activity_to_users.py, run_discount_migration.py
├── create_admin.py, quick_admin.py, setup_admin.py   # Admin account helpers
├── download_nltk_data.py         # Downloads the NLTK data the detector needs
└── *.md                          # Implementation notes for each feature and fix
```

## Prerequisites

| Tool | Version | Check |
|---|---|---|
| Python | 3.9 – 3.12 | `python --version` |
| pip | comes with Python | `pip --version` |
| MySQL Server | 8.0 (or XAMPP / WAMP MySQL) | `mysql --version` |
| C build tools for `mysqlclient` | Windows: usually not needed (wheels); Linux: `sudo apt install python3-dev default-libmysqlclient-dev build-essential pkg-config`; macOS: `brew install mysql pkg-config` | — |
| Groq API key | free at [console.groq.com](https://console.groq.com/keys) | — |
| SMTP account | e.g. Gmail with an App Password | — |
| Git | any | `git --version` |

## Run locally

### 1. Clone and create a virtual environment

```bash
git clone https://github.com/ChanithW/Shopping_Cart_Recovery_AI_Project.git
cd Shopping_Cart_Recovery_AI_Project

python -m venv venv
venv\Scripts\activate            # Windows
# source venv/bin/activate       # macOS / Linux
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
pip install mysqlclient nltk
python download_nltk_data.py
```

If `pip` stops at `MySQLdb==1.4.6` (that name isn't on PyPI), delete that line from `requirements.txt` — `mysqlclient` provides `MySQLdb` — and run the install again.

### 3. Create the database

```bash
mysql -u root -p -e "CREATE DATABASE ecommerce CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -u root -p ecommerce < schema.sql
```

`schema.sql` is the SQL in [Database schema](#database-schema) below — save it to a file first, or paste it into MySQL Workbench / phpMyAdmin.

### 4. Create the `.env` file

Create `.env` in the project root (see [Environment variables](#environment-variables)).

### 5. Create the admin account

```bash
python quick_admin.py
```

### 6. Start the app

```bash
mkdir -p static/images/products     # Windows: mkdir static\images\products
python app.py
```

Open **http://127.0.0.1:8080**. The terminal shows `Cart Abandonment Detector started in background`.

**Try the recovery flow:** register a customer with a real email address, add products to the cart, then stay idle for about a minute. The detector sends the recovery email; opening it updates the log (visible in the admin panel).

## Environment variables

`.env` (loaded with `python-dotenv`):

```env
# Flask
SECRET_KEY=change-me-to-a-long-random-string

# MySQL
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DB=ecommerce

# Email (Gmail example — use an App Password, not your normal password)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=your.address@gmail.com
MAIL_PASSWORD=your_16_char_app_password
MAIL_DEFAULT_SENDER=your.address@gmail.com

# AI cart recovery
GROQ_API_KEY=your_groq_api_key
BASE_URL=http://127.0.0.1:8080
```

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Flask session signing — set your own |
| `MYSQL_*` | Database connection (default database `ecommerce`) |
| `MAIL_*` | SMTP used for recovery and admin emails |
| `GROQ_API_KEY` | Groq API key for writing recovery emails |
| `BASE_URL` | Public URL used in email links and the tracking pixel |

Gmail App Password: Google Account → Security → 2-Step Verification → **App passwords**. More options are in [`EMAILJS_SETUP.md`](EMAILJS_SETUP.md).

## Database schema

The SQL file used to build the database isn't included in the repository. This schema matches the tables and columns the code uses; the detector creates `cart_abandonment_log` automatically on first run.

```sql
CREATE TABLE users (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  name          VARCHAR(100) NOT NULL,
  email         VARCHAR(150) NOT NULL UNIQUE,
  password      VARCHAR(255) NOT NULL,
  role          ENUM('customer','admin') NOT NULL DEFAULT 'customer',
  phone         VARCHAR(30),
  address       TEXT,
  created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_activity TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE products (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  name        VARCHAR(200) NOT NULL,
  description TEXT,
  price       DECIMAL(10,2) NOT NULL,
  stock       INT NOT NULL DEFAULT 0,
  category    VARCHAR(100),
  image       VARCHAR(255),
  created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cart (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  user_id    INT NOT NULL,
  product_id INT NOT NULL,
  quantity   INT NOT NULL DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id)    REFERENCES users(id)    ON DELETE CASCADE,
  FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE TABLE orders (
  id             VARCHAR(36) PRIMARY KEY,          -- UUID
  user_id        INT NOT NULL,
  total_amount   DECIMAL(10,2) NOT NULL,
  status         VARCHAR(30) NOT NULL DEFAULT 'pending',
  payment_status VARCHAR(30) DEFAULT 'pending',
  created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE order_items (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  order_id   VARCHAR(36) NOT NULL,
  product_id INT NOT NULL,
  quantity   INT NOT NULL,
  price      DECIMAL(10,2) NOT NULL,
  FOREIGN KEY (order_id)   REFERENCES orders(id)   ON DELETE CASCADE,
  FOREIGN KEY (product_id) REFERENCES products(id)
);
```

Upgrading an older database: `python migrations/add_last_activity_to_users.py` and `python migrations/run_discount_migration.py`.

## Admin account

```bash
python quick_admin.py
```

Creates (or promotes) **admin@ecommerce.com** / **admin123**. Sign in at http://127.0.0.1:8080/login, then open `/admin`. **Change this password before deploying.** `create_admin.py` and `setup_admin.py` let you create an admin with your own details.

## Routes

**Store**

| Route | Page |
|---|---|
| `/` | Home |
| `/login`, `/register`, `/logout` | Accounts |
| `/profile`, `/delete_account` | Profile |
| `/products`, `/product/<id>` | Catalogue |
| `/cart`, `/add_to_cart`, `/update_cart`, `/remove_from_cart`, `/api/cart/count` | Cart |
| `/checkout`, `/order_success/<order_id>` | Checkout |
| `/orders`, `/cancel_order/<order_id>` | My orders |
| `/track/email/<log_id>` | Email open tracking pixel |

**Admin** (role `admin` only)

| Route | Page |
|---|---|
| `/admin` | Dashboard |
| `/admin/products`, `/admin/add_product`, `/admin/view_product/<id>`, `/admin/edit_product/<id>`, `/admin/delete_product/<id>` | Products |
| `/admin/orders`, `/admin/order_details/<id>`, `/admin/update_order_status`, `/admin/print_order/<id>`, `/admin/export_orders` | Orders |
| `/admin/customers`, `/admin/customer_details/<id>`, `/admin/send_customer_email` | Customers |
| `/admin/email_templates`, `/admin/email_template/<name>` | Email templates |
| `/admin/reports`, `/admin/settings` | Reports, settings |

## Tuning the detector

`cart_abandonment_detector/config.py`:

| Setting | Default | Meaning |
|---|---|---|
| `ABANDONMENT_THRESHOLD_MINUTES` | `1` | Idle time before a cart counts as abandoned (raise to 30–60 for real use) |
| `CHECK_INTERVAL_SECONDS` | `30` | How often carts are checked |
| `DISCOUNT_TIER_1_AMOUNT` / `_PERCENT` | `100` / `10` | 10% off carts over $100 |
| `DISCOUNT_TIER_2_AMOUNT` / `_PERCENT` | `500` / `20` | 20% off carts over $500 |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | LLM used to write emails |
| `SIMILARITY_THRESHOLD` | `0.01` | Minimum similarity for recommendations |

## Production server

```bash
python production_server.py      # Waitress on http://localhost:8080
```

On Windows you can also run `start_production.bat`. On Linux, Gunicorn works too:

```bash
gunicorn -w 4 -b 0.0.0.0:8080 wsgi:application
```

Use `.env.production` as a template, set `BASE_URL` to your public URL, and keep a single app process running the detector so emails aren't sent twice.

## Troubleshooting

| Problem | Fix |
|---|---|
| `ERROR: No matching distribution found for MySQLdb==1.4.6` | Remove that line from `requirements.txt` and `pip install mysqlclient` |
| `mysqlclient` fails to build | Install the MySQL client headers (see Prerequisites) |
| `(1045) Access denied for user 'root'` | Fix `MYSQL_USER` / `MYSQL_PASSWORD` in `.env` |
| `(1146) Table 'ecommerce.users' doesn't exist` | Create the tables from the schema above |
| `LookupError: Resource punkt not found` | `python download_nltk_data.py` |
| Recovery emails never arrive | Check `MAIL_*` settings (Gmail needs an App Password), check spam, make sure the customer was idle long enough |
| Emails are generic / AI error in the log | Set `GROQ_API_KEY`; check your Groq quota |
| Two emails for one cart | Only run one app process; don't run `run_detector.py` alongside `app.py` |
| Product images don't show | Create `static/images/products` |
| Port 8080 already in use | Change the port at the bottom of `app.py` (and `BASE_URL`) |

## More documentation

| File | Topic |
|---|---|
| [`cart_abandonment_detector/ARCHITECTURE.md`](cart_abandonment_detector/ARCHITECTURE.md) | Detector design |
| [`cart_abandonment_detector/COMPLETE_GUIDE.md`](cart_abandonment_detector/COMPLETE_GUIDE.md) | Full detector guide |
| [`cart_abandonment_detector/ADMIN_DASHBOARD.md`](cart_abandonment_detector/ADMIN_DASHBOARD.md) | Admin dashboard metrics |
| [`EMAIL_TRACKING_SYSTEM.md`](EMAIL_TRACKING_SYSTEM.md) | Open tracking |
| [`DISCOUNT_FEATURE_IMPLEMENTATION.md`](DISCOUNT_FEATURE_IMPLEMENTATION.md) | Discount tiers |
| [`DYNAMIC_RECOMMENDATIONS_IMPLEMENTATION.md`](DYNAMIC_RECOMMENDATIONS_IMPLEMENTATION.md) | Recommendations |
| [`IDLE_DETECTION_IMPLEMENTATION.md`](IDLE_DETECTION_IMPLEMENTATION.md) | Idle detection |
| [`EMAILJS_SETUP.md`](EMAILJS_SETUP.md) | Email configuration |

---

Shopping Cart Recovery AI team
