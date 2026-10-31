
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = "shopsphere_secret_key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///shopsphere.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# USER DATABASE TABLE
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# SAMPLE PRODUCTS
products = [
    {"id": 1, "name": "Wireless Headphones", "category": "Electronics",
     "price": 1499, "old_price": 2499, "rating": 4.5, "discount": "40% OFF",
     "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600"},

    {"id": 2, "name": "Classic Wrist Watch", "category": "Fashion",
     "price": 999, "old_price": 1999, "rating": 4.3, "discount": "50% OFF",
     "image": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600"},

    {"id": 3, "name": "Stylish Sneakers", "category": "Fashion",
     "price": 1799, "old_price": 2999, "rating": 4.6, "discount": "40% OFF",
     "image": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=600"},

    {"id": 4, "name": "Modern Backpack", "category": "Accessories",
     "price": 899, "old_price": 1499, "rating": 4.2, "discount": "40% OFF",
     "image": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600"},

    {"id": 5, "name": "Smartphone", "category": "Electronics",
     "price": 14999, "old_price": 17999, "rating": 4.7, "discount": "17% OFF",
     "image": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=600"},

    {"id": 6, "name": "Women Handbag", "category": "Accessories",
     "price": 1299, "old_price": 2199, "rating": 4.4, "discount": "40% OFF",
     "image": "https://images.unsplash.com/photo-1584917865442-de89df76afd3?w=600"},

    {"id": 7, "name": "Sunglasses", "category": "Fashion",
     "price": 599, "old_price": 999, "rating": 4.1, "discount": "40% OFF",
     "image": "https://images.unsplash.com/photo-1511499767150-a48a237f0083?w=600"},

    {"id": 8, "name": "Camera", "category": "Electronics",
     "price": 24999, "old_price": 29999, "rating": 4.8, "discount": "17% OFF",
     "image": "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=600"}
]


@app.route("/")
def home():
    search = request.args.get("search", "")
    category = request.args.get("category", "")

    filtered_products = products

    if search:
        filtered_products = [
            p for p in filtered_products
            if search.lower() in p["name"].lower()
        ]

    if category:
        filtered_products = [
            p for p in filtered_products
            if p["category"] == category
        ]

    cart = session.get("cart", {})
    cart_count = sum(cart.values())

    return render_template(
        "index.html",
        products=filtered_products,
        cart_count=cart_count,
        search=search
    )


@app.route("/add-to-cart/<int:product_id>")
def add_to_cart(product_id):
    cart = session.get("cart", {})
    key = str(product_id)
    cart[key] = cart.get(key, 0) + 1
    session["cart"] = cart
    return redirect(url_for("home"))


@app.route("/cart")
def view_cart():
    cart = session.get("cart", {})
    cart_items = []
    total = 0

    for product in products:
        quantity = cart.get(str(product["id"]), 0)

        if quantity > 0:
            item = product.copy()
            item["quantity"] = quantity
            item["subtotal"] = product["price"] * quantity
            total += item["subtotal"]
            cart_items.append(item)

    return render_template(
        "cart.html",
        cart_items=cart_items,
        total=total
    )


@app.route("/remove/<int:product_id>")
def remove_from_cart(product_id):
    cart = session.get("cart", {})
    cart.pop(str(product_id), None)
    session["cart"] = cart
    return redirect(url_for("view_cart"))


# REGISTER
@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("Please fill all fields.")
            return redirect(url_for("register"))

        if len(password) < 6:
            flash("Password must be at least 6 characters.")
            return redirect(url_for("register"))

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash("This email is already registered. Please login.")
            return redirect(url_for("login"))

        new_user = User(
            name=name,
            email=email,
            password=generate_password_hash(password)
        )

        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        flash("Account created successfully!")
        return redirect(url_for("home"))

    return render_template("register.html")


# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("home"))

        flash("Incorrect email or password.")

    return render_template("login.html")


# LOGOUT
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)
