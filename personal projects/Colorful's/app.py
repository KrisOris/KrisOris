from datetime import datetime
from flask import Flask, render_template, session, redirect, url_for, g, request, flash
from database import get_db, close_db
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash 
from forms import RegistrationForm, LoginForm, CheckoutForm, AccountForm, AddProductForm
from functools import wraps

app = Flask (__name__)
app.teardown_appcontext (close_db)
app.config["SECRET_KEY"] = "this-is-my-secret-key"
app.config ["SESSION_PERMANENT"] = False 
app.config ["SESSION_TYPE"] = "filesystem" 
Session(app)



def ensure_points_schema(db):
    users_cols = [row["name"] for row in db.execute("PRAGMA table_info(users);")]
    if "points_balance" not in users_cols:
        db.execute(
            """ALTER TABLE users
               ADD COLUMN points_balance INTEGER NOT NULL DEFAULT 0;"""
        )
        db.commit()

    orders_cols = [row["name"] for row in db.execute("PRAGMA table_info(orders);")]
    if "points_used" not in orders_cols:
        db.execute(
            """ALTER TABLE orders
               ADD COLUMN points_used INTEGER NOT NULL DEFAULT 0;"""
        )
        db.commit()
    if "points_earned" not in orders_cols:
        db.execute(
            """ALTER TABLE orders
               ADD COLUMN points_earned INTEGER NOT NULL DEFAULT 0;"""
        )
        db.commit()

@app.before_request
def load_logged_in_user():
    g.user = session.get("user_id", None)
    g.is_admin = False
    if g.user is not None:
        db = get_db()
        ensure_points_schema(db)
        row = db.execute(
            """SELECT admin_status FROM users WHERE user_id = ?;""",
            (g.user,),
        ).fetchone()
        if row and row["admin_status"]:
            g.is_admin = True

def login_required(view):
    @wraps (view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            return redirect(url_for("auth", next=request.url))
        return view(*args, **kwargs)
    return wrapped_view

def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            return redirect(url_for("auth", next=request.url))
        if not g.is_admin:
            return redirect(url_for("index"))
        return view(*args, **kwargs)
    return wrapped_view

def verify_password(stored, password):
    """Check password against stored value (hash or plain)."""
    return check_password_hash(stored, password) or (stored == password)

def get_cart():
    """
    Cart is stored in session as { "<product_id>": <qty int> }.
    We normalize keys/values to keep templates + routes consistent.
    """
    cart = session.get("cart")
    if not isinstance(cart, dict):
        cart = {}

    normalized = {}
    for k, v in cart.items():
        try:
            pid = str(int(k))
        except (TypeError, ValueError):
            continue
        try:
            qty = int(v)
        except (TypeError, ValueError):
            qty = 1
        if qty < 1:
            continue
        normalized[pid] = qty

    session["cart"] = normalized
    return normalized





@app.route("/")
def index():
    db = get_db()
    products = db.execute(
        """SELECT * FROM products;"""
    ).fetchmany(3)
    reviews = db.execute(
        """SELECT r.rating, r.comment, r.created_at, r.user_id
                 , o.order_id
           FROM reviews r
           JOIN orders o ON o.order_id = r.order_id
           ORDER BY r.created_at DESC
           LIMIT 5;"""
    ).fetchall()
    return render_template("index.html", products=products, reviews=reviews)






@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    form = AccountForm()
    db = get_db()
    user_row = db.execute(
        """SELECT password, admin_status, points_balance FROM users WHERE user_id = ?;""",
        (g.user,),
    ).fetchone()

    if form.validate_on_submit():
        password_ok = verify_password(user_row["password"], form.current_password.data)
        if not password_ok:
            form.current_password.errors.append("Incorrect current password")
        else:
            new_username = (form.new_username.data or "").strip()
            new_password = form.new_password.data or ""

            if new_username and new_username != g.user:
                conflict = db.execute(
                    """SELECT 1 FROM users WHERE user_id = ?;""", (new_username,)
                ).fetchone()
                if conflict:
                    form.new_username.errors.append("Username already taken")
                else:
                    db.execute(
                        """UPDATE users SET user_id = ? WHERE user_id = ?;""",
                        (new_username, g.user),
                    )
                    db.execute(
                        """UPDATE favourites SET user_id = ? WHERE user_id = ?;""",
                        (new_username, g.user),
                    )
                    db.execute(
                        """UPDATE orders SET user_id = ? WHERE user_id = ?;""",
                        (new_username, g.user),
                    )
                    session["user_id"] = new_username

            if new_password:
                if user_row["admin_status"]:
                    stored_password = new_password
                else:
                    stored_password = generate_password_hash(new_password)
                db.execute(
                    """UPDATE users SET password = ? WHERE user_id = ?;""",
                    (stored_password, new_username if new_username else g.user),
                )

            if not form.new_username.errors:
                db.commit()
                return redirect(url_for("account"))

    points_balance = user_row["points_balance"] if user_row else 0
    return render_template("account.html", form=form, points_balance=points_balance)

@app.route("/auth", methods=["GET", "POST"])
def auth():
    login_form = LoginForm(prefix="login")
    register_form = RegistrationForm(prefix="register")
    next_page = request.args.get("next") or request.form.get("next")

    if request.method == "POST":
        if login_form.submit.data:
            if login_form.validate():
                user_id = login_form.user_id.data
                password = login_form.password.data
                db = get_db()
                matching_user = db.execute(
                    """SELECT * FROM users WHERE user_id = ?;""",
                    (user_id,),
                ).fetchone()
                if matching_user is None:
                    login_form.user_id.errors.append("Unknown user id")
                else:
                    password_ok = verify_password(matching_user["password"], password)
                    if not password_ok:
                        login_form.password.errors.append("Incorrect password")
                    else:
                        session.clear()
                        session["user_id"] = user_id
                        return redirect(next_page or url_for("index"))
        elif register_form.submit.data:
            if register_form.validate():
                user_id = register_form.user_id.data
                password = register_form.password.data
                db = get_db()
                conflict = db.execute(
                    """SELECT * FROM users WHERE user_id = ?;""",
                    (user_id,),
                ).fetchone()
                if conflict is not None:
                    register_form.user_id.errors.append("User id conflicts with another")
                else:
                    db.execute(
                        """INSERT INTO users (user_id, password, admin_status) VALUES (?, ?, ?);""",
                        (user_id, generate_password_hash(password), False),
                    )
                    db.commit()

                    session.clear()
                    session["user_id"] = user_id
                    return redirect(next_page or url_for("index"))

    return render_template(
        "auth.html",
        login_form=login_form,
        register_form=register_form,
        next_page=next_page
    )

@app.route("/logout") 
@login_required
def logout():
    session.clear()
    return redirect(url_for("index"))







@app.route("/products")
def products():
    db = get_db()
    search = (request.args.get("q") or "").strip()
    message = None

    if search:
        like = f"%{search}%"
        products = db.execute(
            """
            SELECT * FROM products
            WHERE name LIKE ? OR description LIKE ?;
            """,
            (like, like),
        ).fetchall()
        if not products:
            message = "No products match your search. Try a different name or keyword."
    else:
        products = db.execute(
            """
            SELECT * FROM products;
            """
        ).fetchall()

    return render_template(
        "products.html",
        products=products,
        search_query=search,
        message=message,
    )

@app.route("/product/<int:product_id>")
def product(product_id):
    db = get_db()
    product = db.execute("""
        SELECT * FROM products
        WHERE product_id = ?;""", 
        (product_id,)).fetchone()

    suggestions = db.execute("""
        SELECT * FROM products 
        WHERE product_id != ? ;""", 
        (product_id,)).fetchmany(4)
    is_favourite = False
    if g.user is not None:
        is_favourite = (
            db.execute(
                """SELECT 1 FROM favourites
                   WHERE user_id = ? AND product_id = ?;""",
                (g.user, product_id),
            ).fetchone()
            is not None
        )

    return render_template(
        "product.html",
        product=product,
        suggestions=suggestions,
        is_favourite=is_favourite,
    )









@app.route("/cart")
@login_required
def cart():
    cart_data = get_cart()
    names = {}
    images = {}
    prices = {}
    cart_total = 0
    cart_items = []
    db = get_db()
    for product_id in cart_data:
        pid_int = int(product_id)
        product = db.execute(
            """SELECT * FROM products
               WHERE product_id = ?;""",
            (pid_int,),
        ).fetchone()
        if product is None:
            continue
        names[product_id] = product["name"]
        images[product_id] = product["image_filename"]
        prices[product_id] = float(product["price"])
        cart_total += prices[product_id] * cart_data[product_id]
        cart_items.append(product_id)

    cart_total = round(cart_total, 2)

    return render_template(
        "cart.html",
        cart=cart_data,
        cart_items=cart_items,
        names=names,
        images=images,
        prices=prices,
        cart_total=cart_total
    )

@app.route("/add_to_cart/<int:product_id>")
@login_required
def add_to_cart(product_id):
    cart_data = get_cart()
    pid = str(product_id)
    db = get_db()
    product = db.execute(
        """SELECT quantity FROM products WHERE product_id = ?;""",
        (product_id,),
    ).fetchone()
    current_qty = cart_data.get(pid, 0)
    if product is None or product["quantity"] <= current_qty:
        flash("Can't increase the quantity of product, because we dont have enough in stock.")
    else:
        cart_data[pid] = current_qty + 1
        session["cart"] = cart_data
    return redirect(url_for("cart"))


@app.route("/increase_cart/<int:product_id>")
@login_required
def increase_cart(product_id):
    cart_data = get_cart()
    pid = str(product_id)
    db = get_db()
    product = db.execute(
        """SELECT quantity FROM products WHERE product_id = ?;""",
        (product_id,),
    ).fetchone()
    current_qty = cart_data.get(pid, 0)
    if product is None or product["quantity"] <= current_qty:
        flash("Can't increase the quantity of product, because we dont have enough in stock.")
    else:
        cart_data[pid] = current_qty + 1
        session["cart"] = cart_data
    return redirect(url_for("cart"))


@app.route("/decrease_cart/<int:product_id>")
@login_required
def decrease_cart(product_id):
    cart_data = get_cart()
    pid = str(product_id)
    if pid in cart_data:
        if cart_data[pid] <= 1:
            cart_data.pop(pid, None)
        else:
            cart_data[pid] = cart_data[pid] - 1
    session["cart"] = cart_data
    return redirect(url_for("cart"))


@app.route("/remove_from_cart/<int:product_id>")
@login_required
def remove_from_cart(product_id):
    cart_data = get_cart()
    cart_data.pop(str(product_id), None)
    session["cart"] = cart_data
    return redirect(url_for("cart"))


@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    cart_data = get_cart()
    if not cart_data:
        return redirect(url_for("cart"))

    db = get_db()
    ensure_points_schema(db)
    names = {}
    prices = {}
    cart_total = 0
    cart_items = []
    for product_id in cart_data:
        pid_int = int(product_id)
        product = db.execute(
            """SELECT * FROM products WHERE product_id = ?;""",
            (pid_int,),
        ).fetchone()
        if product is None:
            continue
        if product["quantity"] < cart_data[product_id]:
            flash(f"Not enough stock for {product['name']}. Please reduce quantity in your cart.")
            return redirect(url_for("cart"))
        names[product_id] = product["name"]
        prices[product_id] = float(product["price"])
        cart_total += prices[product_id] * cart_data[product_id]
        cart_items.append(product_id)
    cart_total = round(cart_total, 2)

    form = CheckoutForm()
    if form.validate_on_submit():
        order_date = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        db.execute(
            """INSERT INTO orders (user_id, order_date, address, city, postal_code, country, status)
               VALUES (?, ?, ?, ?, ?, ?, 'active');""",
            (g.user, order_date, form.address.data, form.city.data,
             form.postal_code.data, form.country.data),
        )
        order_id = db.execute("SELECT last_insert_rowid();").fetchone()[0]
        for product_id in cart_items:
            pid_int = int(product_id)
            qty = cart_data[product_id]
            db.execute(
                """INSERT INTO order_items (order_id, product_id, quantity, unit_price)
                   VALUES (?, ?, ?, ?);""",
                (order_id, pid_int, qty, prices[product_id]),
            )
            db.execute(
                """UPDATE products
                   SET quantity = quantity - ?
                   WHERE product_id = ?;""",
                (qty, pid_int),
            )
        user_row = db.execute(
            """SELECT points_balance FROM users WHERE user_id = ?;""",
            (g.user,),
        ).fetchone()
        current_points = user_row["points_balance"] if user_row else 0

        requested_points = form.redeem_points.data or 0
        if requested_points < 0:
            requested_points = 0

        max_points_by_total = int(cart_total / 0.20) if cart_total > 0 else 0
        max_redeemable_points = min(current_points, max_points_by_total)

        if requested_points > max_redeemable_points:
            form.redeem_points.errors.append(
                f"You can redeem at most {max_redeemable_points} points for this order."
            )
            db.rollback()
            return render_template(
                "checkout.html",
                form=form,
                cart=cart_data,
                cart_items=cart_items,
                names=names,
                prices=prices,
                cart_total=cart_total,
                points_balance=current_points,
                max_redeemable_points=max_redeemable_points,
            )

        discount_amount = requested_points * 0.20
        final_total = cart_total - discount_amount
        if final_total < 0:
            final_total = 0.0

        db.execute(
            """UPDATE orders
               SET points_used = ?
               WHERE order_id = ?;""",
            (requested_points, order_id),
        )
        if requested_points > 0:
            db.execute(
                """UPDATE users
                   SET points_balance = points_balance - ?
                   WHERE user_id = ?;""",
                (requested_points, g.user),
            )

        db.commit()
        session["cart"] = {}
        return redirect(url_for("orders"))

    user_row = db.execute(
        """SELECT points_balance FROM users WHERE user_id = ?;""",
        (g.user,),
    ).fetchone()
    points_balance = user_row["points_balance"] if user_row else 0
    max_points_by_total = int(cart_total / 0.20) if cart_total > 0 else 0
    max_redeemable_points = min(points_balance, max_points_by_total)

    return render_template(
        "checkout.html",
        form=form,
        cart=cart_data,
        cart_items=cart_items,
        names=names,
        prices=prices,
        cart_total=cart_total,
        points_balance=points_balance,
        max_redeemable_points=max_redeemable_points,
    )













@app.route("/favorites")
@login_required
def favorites():
    db = get_db()
    favourites = db.execute(
        """
        SELECT p.*
        FROM products p
        JOIN favourites f ON f.product_id = p.product_id
        WHERE f.user_id = ?
        ORDER BY p.name;
        """,
        (g.user,),
    ).fetchall()
    return render_template("favorites.html", favourites=favourites)


@app.route("/add_to_favorites/<int:product_id>")
@login_required
def add_to_favorites(product_id):
    db = get_db()
    db.execute(
        """INSERT OR IGNORE INTO favourites (user_id, product_id)
           VALUES (?, ?);""",
        (g.user, product_id),
    )
    db.commit()
    return redirect(url_for("favorites"))


@app.route("/remove_favorite/<int:product_id>")
@login_required
def remove_favorite(product_id):
    db = get_db()
    db.execute(
        """DELETE FROM favourites
           WHERE user_id = ? AND product_id = ?;""",
        (g.user, product_id),
    )
    db.commit()
    return redirect(url_for("favorites"))












@app.route("/orders")
@login_required
def orders():
    db = get_db()
    orders_list = db.execute(
        """SELECT order_id, order_date, address, city, postal_code, country, status, admin_note,
                  points_used, points_earned
           FROM orders
           WHERE user_id = ?
           ORDER BY order_date DESC;""",
        (g.user,),
    ).fetchall()
    reviews_map = {}
    reviews = db.execute(
        """SELECT review_id, order_id, rating, comment, created_at
           FROM reviews
           WHERE user_id = ?;""",
        (g.user,),
    ).fetchall()
    for r in reviews:
        reviews_map[r["order_id"]] = r
    order_items_map = {}
    for order in orders_list:
        items = db.execute(
            """SELECT oi.product_id, oi.quantity, oi.unit_price, p.name
               FROM order_items oi
               JOIN products p ON p.product_id = oi.product_id
               WHERE oi.order_id = ?;""",
            (order["order_id"],),
        ).fetchall()
        order_items_map[order["order_id"]] = items
    return render_template(
        "orders.html",
        orders_list=orders_list,
        order_items_map=order_items_map,
        reviews_map=reviews_map,
    )

@app.route("/orders/cancel/<int:order_id>", methods=["POST"])
@login_required
def cancel_order(order_id):
    db = get_db()
    ensure_points_schema(db)
    order = db.execute(
        """SELECT status, user_id, points_used FROM orders WHERE order_id = ?;""",
        (order_id,),
    ).fetchone()
    if order is None:
        return redirect(url_for("admin_manage_users" if g.is_admin else "orders"))
    if (not g.is_admin) and order["user_id"] != g.user:
        return redirect(url_for("orders"))
    if order["status"] != "active":
        return redirect(url_for("admin_manage_users" if g.is_admin else "orders"))

    items = db.execute(
        """SELECT product_id, quantity
           FROM order_items
           WHERE order_id = ?;""",
        (order_id,),
    ).fetchall()
    for item in items:
        db.execute(
            """UPDATE products
               SET quantity = quantity + ?
               WHERE product_id = ?;""",
            (item["quantity"], item["product_id"]),
        )
   

    points_used = order["points_used"] or 0
    if points_used > 0:
        db.execute(
            """UPDATE users
               SET points_balance = points_balance + ?
               WHERE user_id = ?;""",
            (points_used, order["user_id"]),
        )
        db.execute(
            """UPDATE orders
               SET points_used = 0
               WHERE order_id = ?;""",
            (order_id,),
        )
    db.execute(
        """UPDATE orders
           SET status = 'cancelled'
           WHERE order_id = ?;""",
        (order_id,),
    )
    db.commit()
    if g.is_admin:
        return redirect(url_for("admin_manage_users"))
    else:
        return redirect(url_for("orders"))

@app.route("/orders/review/<int:order_id>", methods=["POST"])
@login_required
def review_order(order_id):
    db = get_db()
    order = db.execute(
        """SELECT user_id, status FROM orders WHERE order_id = ?;""",
        (order_id,),
    ).fetchone()
    if order is None or order["user_id"] != g.user or order["status"] != "delivered":
        return redirect(url_for("orders"))

    existing = db.execute(
        """SELECT 1 FROM reviews WHERE order_id = ? AND user_id = ?;""",
        (order_id, g.user),
    ).fetchone()
    if existing:
        return redirect(url_for("orders"))

    try:
        rating = int(request.form.get("rating", "0"))
    except ValueError:
        rating = 0
    comment = (request.form.get("comment") or "").strip()
    if rating < 1 or rating > 5:
        flash("Please select a rating from 1 to 5.")
        return redirect(url_for("orders"))

    created_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    db.execute(
        """INSERT INTO reviews (order_id, user_id, rating, comment, created_at)
           VALUES (?, ?, ?, ?, ?);""",
        (order_id, g.user, rating, comment, created_at),
    )
    db.commit()
    return redirect(url_for("orders"))








@app.route("/admin")
@admin_required
def admin_dashboard():

    db = get_db()

    products_count = db.execute("SELECT COUNT(*) FROM products;").fetchone()[0]
    users_count = db.execute("SELECT COUNT(*) FROM users;").fetchone()[0]
    orders_count = db.execute("SELECT COUNT(*) FROM orders;").fetchone()[0]

    reviews = db.execute(
        """SELECT r.rating, r.comment, r.created_at, r.user_id
                 , o.order_id
           FROM reviews r
           JOIN orders o ON o.order_id = r.order_id
           ORDER BY r.created_at DESC   ;"""
    ).fetchall()

    return render_template(
        "admin_dashboard.html",
        products_count=products_count,
        users_count=users_count,
        orders_count=orders_count,
        reviews = reviews,
    )

@app.route("/user_menu")
@login_required
def user_menu():
    return render_template("user_menu.html")

@app.route("/admin/products", methods=["GET", "POST"])
@admin_required
def admin_manage_products():
    form = AddProductForm()
    db = get_db()
    if form.validate_on_submit():
        db.execute(
            """INSERT INTO products (name, price, image_filename, quantity, description)
               VALUES (?, ?, ?, ?, ?);""",
            (
                form.name.data,
                form.price.data,
                form.image_filename.data.strip(),
                form.quantity.data,
                form.description.data or "",
            ),
        )
        db.commit()
        return redirect(url_for("admin_manage_products"))
    products = db.execute("SELECT * FROM products ORDER BY product_id;").fetchall()
    return render_template("admin_manage_products.html", form=form, products=products)

@app.route("/admin/products/delete/<int:product_id>", methods=["POST"])
@admin_required
def admin_delete_product(product_id):
    db = get_db()
    in_orders = db.execute(
        """SELECT 1 FROM order_items WHERE product_id = ?;""", (product_id,)
    ).fetchone()
    if in_orders:
        flash("Cannot delete product: it appears in existing orders.")
        return redirect(url_for("admin_manage_products"))
    db.execute("DELETE FROM favourites WHERE product_id = ?;", (product_id,))
    db.execute("DELETE FROM products WHERE product_id = ?;", (product_id,))
    db.commit()
    return redirect(url_for("admin_manage_products"))

@app.route("/admin/products/update-quantity/<int:product_id>", methods=["POST"])
@admin_required
def admin_update_product_quantity(product_id):
    db = get_db()
    try:
        new_qty = int(request.form.get("quantity", "0"))
    except ValueError:
        new_qty = 0
    if new_qty < 0:
        new_qty = 0
    db.execute(
        """UPDATE products
           SET quantity = ?
           WHERE product_id = ?;""",
        (new_qty, product_id),
    )
    db.commit()
    return redirect(url_for("admin_manage_products"))

@app.route("/admin/orders_and_users")
@admin_required
def admin_manage_users():
    db = get_db()
    search = request.args.get("q", "").strip()
    if search:
        users = db.execute(
            """SELECT user_id, admin_status, points_balance FROM users
               WHERE user_id LIKE ? ORDER BY user_id;""",
            (f"%{search}%",),
        ).fetchall()
    else:
        users = db.execute(
            """SELECT user_id, admin_status, points_balance FROM users ORDER BY user_id;"""
        ).fetchall()
    users_data = []
    for user in users:
        orders = db.execute(
            """SELECT order_id, order_date, address, city, postal_code, country, status, admin_note,
                      points_used, points_earned
               FROM orders WHERE user_id = ? ORDER BY order_date DESC;""",
            (user["user_id"],),
        ).fetchall()
        order_items_map = {}
        for order in orders:
            items = db.execute(
                """SELECT oi.product_id, oi.quantity, oi.unit_price, p.name
                   FROM order_items oi
                   JOIN products p ON p.product_id = oi.product_id
                   WHERE oi.order_id = ?;""",
                (order["order_id"],),
            ).fetchall()
            order_items_map[order["order_id"]] = items
        users_data.append({
            "user": user,
            "orders": orders,
            "order_items_map": order_items_map,
        })
    return render_template(
        "admin_manage_users.html",
        users_data=users_data,
        search_query=search,
    )

@app.route("/admin/users/toggle-admin", methods=["POST"])
@admin_required
def admin_toggle_admin():
    target_user = request.form.get("user_id")
    search = request.form.get("q", "").strip()
    redirect_url = url_for("admin_manage_users")
    if search:
        redirect_url = url_for("admin_manage_users", q=search)
    if not target_user:
        return redirect(redirect_url)
    db = get_db()
    row = db.execute(
        """SELECT admin_status FROM users WHERE user_id = ?;""",
        (target_user,),
    ).fetchone()
    if row is None:
        return redirect(redirect_url)
    admin_count = db.execute(
        """SELECT COUNT(*) FROM users WHERE admin_status = 1;"""
    ).fetchone()[0]
    if admin_count <= 1 and row["admin_status"]:
        flash("Cannot remove the last admin.")
        return redirect(redirect_url)
    new_status = not row["admin_status"]
    db.execute(
        """UPDATE users SET admin_status = ? WHERE user_id = ?;""",
        (new_status, target_user),
    )
    db.commit()
    return redirect(redirect_url)

@app.route("/admin/orders/update-note", methods=["POST"])
@admin_required
def admin_update_order_note():
    order_id = request.form.get("order_id")
    search = request.form.get("q", "").strip()
    redirect_url = url_for("admin_manage_users")
    if search:
        redirect_url = url_for("admin_manage_users", q=search)
    if not order_id:
        return redirect(redirect_url)
    db = get_db()
    note = (request.form.get("admin_note") or "").strip()
    db.execute(
        """UPDATE orders
           SET admin_note = ?
           WHERE order_id = ?;""",
        (note, order_id),
    )
    db.commit()
    return redirect(redirect_url)

@app.route("/admin/orders/mark-delivered/<int:order_id>", methods=["POST"])
@admin_required
def admin_mark_order_delivered(order_id):
    db = get_db()
    ensure_points_schema(db)
    order = db.execute(
        """SELECT user_id, status, points_used, points_earned
           FROM orders
           WHERE order_id = ?;""",
        (order_id,),
    ).fetchone()
    if order is None:
        return redirect(url_for("admin_manage_users"))
    if order["status"] != "active":
        return redirect(url_for("admin_manage_users"))

    row = db.execute(
        """SELECT SUM(quantity * unit_price) AS total
           FROM order_items
           WHERE order_id = ?;""",
        (order_id,),
    ).fetchone()
    order_total = row["total"] or 0.0
    net_total = order_total - (order["points_used"] * 0.20)
    if net_total < 0:
        net_total = 0.0
    points_earned = int(net_total)

    if points_earned > 0:
        db.execute(
            """UPDATE users
               SET points_balance = points_balance + ?
               WHERE user_id = ?;""",
            (points_earned, order["user_id"]),
        )
    db.execute(
        """UPDATE orders
           SET status = 'delivered',
               points_earned = ?
           WHERE order_id = ?;""",
        (points_earned, order_id),
    )
    db.commit()
    return redirect(url_for("admin_manage_users"))

@app.route("/admin/reviews")
@admin_required
def admin_reviews():
    db = get_db()
    reviews = db.execute(
        """SELECT r.review_id, r.order_id, r.user_id, r.rating, r.comment, r.created_at
                 , o.order_date
           FROM reviews r
           JOIN orders o ON o.order_id = r.order_id
           ORDER BY r.created_at DESC;"""
    ).fetchall()
    return render_template("admin_reviews.html", reviews=reviews)

@app.route("/admin/reviews/delete/<int:review_id>", methods=["POST"])
@admin_required
def admin_delete_review(review_id):
    db = get_db()
    db.execute(
        """DELETE FROM reviews WHERE review_id = ?;""",
        (review_id,),
    )
    db.commit()
    return redirect(url_for("admin_reviews"))

