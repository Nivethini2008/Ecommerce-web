import os
from datetime import datetime
from functools import wraps

from flask import Flask, jsonify, redirect, render_template, request, session, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-secret-key")

# Default database is SQLite. You can use MySQL/PostgreSQL by setting DATABASE_URL.
# Examples:
# MySQL: mysql+pymysql://root:password@localhost/ecommerce_db
# PostgreSQL: postgresql+psycopg2://postgres:password@localhost/ecommerce_db
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///ecommerce.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# -------------------------
# Database models
# -------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="user", nullable=False)

    orders = db.relationship("Order", backref="user", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    category = db.Column(db.String(100), nullable=False, default="General")
    image_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    order_items = db.relationship("OrderItem", backref="product", lazy=True)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(30), default="Pending", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship(
        "OrderItem", backref="order", lazy=True, cascade="all, delete-orphan"
    )


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)


# -------------------------
# Helpers
# -------------------------
def current_user():
    user_id = session.get("user_id")
    return db.session.get(User, user_id) if user_id else None


@app.context_processor
def inject_globals():
    cart = session.get("cart", {})
    cart_count = sum(int(qty) for qty in cart.values())
    return {"current_user": current_user(), "cart_count": cart_count}


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in first.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user or user.role != "admin":
            flash("Admin access is required.", "danger")
            return redirect(url_for("index"))
        return view(*args, **kwargs)
    return wrapped


def get_cart_details():
    cart = session.get("cart", {})
    items = []
    total = 0.0

    for product_id, quantity in cart.items():
        product = db.session.get(Product, int(product_id))
        if not product:
            continue

        quantity = int(quantity)
        subtotal = product.price * quantity
        items.append({
            "product": product,
            "quantity": quantity,
            "subtotal": subtotal
        })
        total += subtotal

    return items, total


def seed_database():
    if not User.query.filter_by(email="admin@example.com").first():
        admin = User(name="Administrator", email="admin@example.com", role="admin")
        admin.set_password("admin123")
        db.session.add(admin)

    if not User.query.filter_by(email="user@example.com").first():
        user = User(name="Demo User", email="user@example.com", role="user")
        user.set_password("user123")
        db.session.add(user)

    if Product.query.count() == 0:
        products = [
            Product(
                name="Wireless Headphones",
                description="Comfortable wireless headphones with clear sound.",
                price=2499,
                stock=20,
                category="Electronics",
                image_url="https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=800&q=80",
            ),
            Product(
                name="Smart Watch",
                description="Fitness tracking and notifications in a modern design.",
                price=3999,
                stock=15,
                category="Electronics",
                image_url="https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=800&q=80",
            ),
            Product(
                name="Running Shoes",
                description="Lightweight everyday running shoes.",
                price=2999,
                stock=25,
                category="Fashion",
                image_url="https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=800&q=80",
            ),
            Product(
                name="Laptop Backpack",
                description="Water-resistant backpack with laptop compartment.",
                price=1599,
                stock=30,
                category="Accessories",
                image_url="https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=800&q=80",
            ),
        ]
        db.session.add_all(products)

    db.session.commit()


# -------------------------
# Main pages
# -------------------------
@app.route("/")
def index():
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()

    query = Product.query
    if search:
        query = query.filter(
            db.or_(
                Product.name.ilike(f"%{search}%"),
                Product.description.ilike(f"%{search}%")
            )
        )
    if category:
        query = query.filter_by(category=category)

    products = query.order_by(Product.created_at.desc()).all()
    categories = [row[0] for row in db.session.query(Product.category).distinct()]

    return render_template(
        "index.html",
        products=products,
        categories=categories,
        search=search,
        selected_category=category
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return redirect(url_for("register"))

        if User.query.filter_by(email=email).first():
            flash("Email is already registered.", "danger")
            return redirect(url_for("register"))

        user = User(name=name, email=email, role="user")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            session["user_id"] = user.id
            flash(f"Welcome, {user.name}!", "success")
            return redirect(url_for("index"))

        flash("Invalid email or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


# -------------------------
# Cart and checkout
# -------------------------
@app.route("/cart")
def cart():
    items, total = get_cart_details()
    return render_template("cart.html", items=items, total=total)


@app.post("/cart/add/<int:product_id>")
def add_to_cart(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        flash("Product not found.", "danger")
        return redirect(url_for("index"))

    if product.stock <= 0:
        flash("This product is out of stock.", "warning")
        return redirect(url_for("index"))

    cart = session.get("cart", {})
    key = str(product_id)
    new_quantity = int(cart.get(key, 0)) + 1

    if new_quantity > product.stock:
        flash("You cannot add more than the available stock.", "warning")
    else:
        cart[key] = new_quantity
        session["cart"] = cart
        session.modified = True
        flash(f"{product.name} added to cart.", "success")

    return redirect(request.referrer or url_for("index"))


@app.post("/cart/update/<int:product_id>")
def update_cart(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        return redirect(url_for("cart"))

    try:
        quantity = int(request.form["quantity"])
    except (ValueError, KeyError):
        quantity = 1

    cart = session.get("cart", {})
    key = str(product_id)

    if quantity <= 0:
        cart.pop(key, None)
    elif quantity <= product.stock:
        cart[key] = quantity
    else:
        flash(f"Only {product.stock} item(s) are available.", "warning")

    session["cart"] = cart
    session.modified = True
    return redirect(url_for("cart"))


@app.post("/cart/remove/<int:product_id>")
def remove_from_cart(product_id):
    cart = session.get("cart", {})
    cart.pop(str(product_id), None)
    session["cart"] = cart
    session.modified = True
    return redirect(url_for("cart"))


@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    items, total = get_cart_details()

    if not items:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("index"))

    if request.method == "POST":
        # Re-check stock before creating the order.
        for item in items:
            if item["quantity"] > item["product"].stock:
                flash(f"Not enough stock for {item['product'].name}.", "danger")
                return redirect(url_for("cart"))

        order = Order(
            user_id=session["user_id"],
            total_amount=total,
            status="Pending"
        )
        db.session.add(order)
        db.session.flush()

        for item in items:
            product = item["product"]
            quantity = item["quantity"]

            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=quantity,
                price=product.price
            )
            product.stock -= quantity
            db.session.add(order_item)

        db.session.commit()
        session["cart"] = {}
        session.modified = True

        flash(f"Order #{order.id} placed successfully.", "success")
        return redirect(url_for("orders"))

    return render_template("checkout.html", items=items, total=total)


@app.route("/orders")
@login_required
def orders():
    user = current_user()
    orders = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).all()
    return render_template("orders.html", orders=orders)


# -------------------------
# Admin dashboard
# -------------------------
@app.route("/admin")
@admin_required
def admin_dashboard():
    products = Product.query.order_by(Product.id.desc()).all()
    orders = Order.query.order_by(Order.created_at.desc()).all()
    users = User.query.order_by(User.id.desc()).all()

    return render_template(
        "admin.html",
        products=products,
        orders=orders,
        users=users
    )


@app.route("/admin/products/add", methods=["GET", "POST"])
@admin_required
def add_product():
    if request.method == "POST":
        product = Product(
            name=request.form["name"].strip(),
            description=request.form["description"].strip(),
            price=float(request.form["price"]),
            stock=int(request.form["stock"]),
            category=request.form["category"].strip() or "General",
            image_url=request.form.get("image_url", "").strip()
        )
        db.session.add(product)
        db.session.commit()
        flash("Product added successfully.", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template("product_form.html", product=None)


@app.route("/admin/products/edit/<int:product_id>", methods=["GET", "POST"])
@admin_required
def edit_product(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        flash("Product not found.", "danger")
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        product.name = request.form["name"].strip()
        product.description = request.form["description"].strip()
        product.price = float(request.form["price"])
        product.stock = int(request.form["stock"])
        product.category = request.form["category"].strip() or "General"
        product.image_url = request.form.get("image_url", "").strip()

        db.session.commit()
        flash("Product updated successfully.", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template("product_form.html", product=product)


@app.post("/admin/products/delete/<int:product_id>")
@admin_required
def delete_product(product_id):
    product = db.session.get(Product, product_id)
    if product:
        if OrderItem.query.filter_by(product_id=product.id).first():
            flash("This product is linked to an existing order and cannot be deleted.", "warning")
        else:
            db.session.delete(product)
            db.session.commit()
            flash("Product deleted.", "success")
    return redirect(url_for("admin_dashboard"))


@app.post("/admin/orders/<int:order_id>/status")
@admin_required
def update_order_status(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        flash("Order not found.", "danger")
        return redirect(url_for("admin_dashboard"))

    allowed = {"Pending", "Processing", "Shipped", "Delivered", "Cancelled"}
    status = request.form.get("status")

    if status in allowed:
        order.status = status
        db.session.commit()
        flash(f"Order #{order.id} status updated.", "success")

    return redirect(url_for("admin_dashboard"))


# -------------------------
# REST API
# -------------------------
@app.get("/api/products")
def api_products():
    products = Product.query.order_by(Product.id.desc()).all()
    return jsonify([
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "price": p.price,
            "stock": p.stock,
            "category": p.category,
            "image_url": p.image_url
        }
        for p in products
    ])


@app.get("/api/products/<int:product_id>")
def api_product(product_id):
    p = db.session.get(Product, product_id)
    if not p:
        return jsonify({"error": "Product not found"}), 404

    return jsonify({
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "price": p.price,
        "stock": p.stock,
        "category": p.category,
        "image_url": p.image_url
    })


@app.get("/api/orders")
@admin_required
def api_orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return jsonify([
        {
            "id": o.id,
            "user_id": o.user_id,
            "total_amount": o.total_amount,
            "status": o.status,
            "created_at": o.created_at.isoformat()
        }
        for o in orders
    ])


# -------------------------
# Error handlers
# -------------------------
@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404


@app.errorhandler(500)
def server_error(error):
    db.session.rollback()
    return render_template("500.html"), 500


# -------------------------
# Start application
# -------------------------
with app.app_context():
    db.create_all()
    seed_database()


if __name__ == "__main__":
    app.run(debug=True)
