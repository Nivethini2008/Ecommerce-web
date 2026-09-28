# E-Commerce Web Application

A beginner-friendly full-stack e-commerce web application built with:

- Python
- Flask
- Flask-SQLAlchemy
- SQLite by default
- MySQL/PostgreSQL support through `DATABASE_URL`
- HTML/CSS/JavaScript
- Role-based access: Admin/User
- Product CRUD
- Shopping cart
- Checkout
- Order tracking
- REST API

## 1. Install Python

Python 3.10+ is recommended.

Check:

```bash
python --version
```

## 2. Create a virtual environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

## 3. Install packages

```bash
pip install -r requirements.txt
```

## 4. Run the application

```bash
python app.py
```

Open:

http://127.0.0.1:5000

## Demo accounts

Admin:

- Email: admin@example.com
- Password: admin123

User:

- Email: user@example.com
- Password: user123

## Database

The application automatically creates `ecommerce.db` using SQLite.

### MySQL

Install the MySQL server and create a database named `ecommerce_db`.

Windows PowerShell:

```powershell
$env:DATABASE_URL="mysql+pymysql://root:YOUR_PASSWORD@localhost/ecommerce_db"
python app.py
```

### PostgreSQL

```powershell
$env:DATABASE_URL="postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost/ecommerce_db"
python app.py
```

## Main routes

- `/` - Product catalog
- `/register` - User registration
- `/login` - Login
- `/cart` - Shopping cart
- `/checkout` - Checkout
- `/orders` - Logged-in user's orders
- `/admin` - Admin dashboard
- `/api/products` - Product API
- `/api/orders` - Admin order API

## Important

This is a learning/project application. For production use, add CSRF protection, secure environment variables, payment-gateway integration, stronger validation, email verification, HTTPS, and proper deployment configuration.
