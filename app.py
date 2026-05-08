from __future__ import annotations

import os
from functools import wraps

import psycopg
from flask import (
    Flask,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from psycopg.rows import dict_row


DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://store_user:store_password@localhost:5432/assignment_store",
)
MANAGER_PASSWORD = os.environ.get("MANAGER_PASSWORD", "admin123")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-me-for-production")


def get_db():
    if "db" not in g:
        g.db = psycopg.connect(DATABASE_URL, row_factory=dict_row)
    return g.db


@app.teardown_appcontext
def close_db(_error):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                create table if not exists products (
                    id serial primary key,
                    name varchar(120) not null unique,
                    category varchar(80) not null,
                    price numeric(10, 2) not null check (price >= 0),
                    stock_status varchar(30) not null,
                    created_at timestamptz not null default now()
                )
                """
            )
            cur.execute(
                """
                create table if not exists orders (
                    id serial primary key,
                    customer_name varchar(120) not null,
                    customer_email varchar(160) not null,
                    product_id integer not null references products(id) on delete restrict,
                    quantity integer not null check (quantity > 0),
                    order_status varchar(30) not null default 'Pending',
                    created_at timestamptz not null default now()
                )
                """
            )
            cur.execute("select count(*) from products")
            if cur.fetchone()[0] == 0:
                cur.executemany(
                    """
                    insert into products (name, category, price, stock_status)
                    values (%s, %s, %s, %s)
                    """,
                    [
                        ("Wireless Headphones", "Electronics", 199.99, "In Stock"),
                        ("Leather Tote Bag", "Fashion", 89.50, "Low Stock"),
                        ("Table Lamp", "Home", 64.00, "In Stock"),
                        ("Skin Serum", "Beauty", 38.75, "In Stock"),
                        ("Yoga Mat", "Sports", 52.25, "Out of Stock"),
                    ],
                )


def manager_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if not session.get("manager_logged_in"):
            flash("Manager login required.", "warning")
            return redirect(url_for("manager_login"))
        return view(**kwargs)

    return wrapped_view


def product_choices():
    return {
        "categories": ["Electronics", "Fashion", "Home", "Beauty", "Sports"],
        "stock_statuses": ["In Stock", "Low Stock", "Out of Stock", "Discontinued"],
        "order_statuses": ["Pending", "Confirmed", "Shipped", "Delivered", "Cancelled"],
    }


@app.context_processor
def inject_choices():
    return product_choices()


@app.get("/health")
def health():
    try:
        get_db().execute("select 1")
        return {"ok": True}
    except Exception as error:
        return {"ok": False, "error": str(error)}, 500


@app.get("/")
def storefront():
    search = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()

    filters = []
    params = []
    if search:
        filters.append("lower(name) like %s")
        params.append(f"%{search.lower()}%")
    if category:
        filters.append("category = %s")
        params.append(category)

    where_clause = f"where {' and '.join(filters)}" if filters else ""
    products = get_db().execute(
        f"""
        select id, name, category, price, stock_status
        from products
        {where_clause}
        order by id desc
        """,
        params,
    ).fetchall()

    return render_template(
        "storefront.html",
        products=products,
        search=search,
        selected_category=category,
    )


@app.post("/orders")
def place_order():
    customer_name = request.form.get("customer_name", "").strip()
    customer_email = request.form.get("customer_email", "").strip()
    product_id = request.form.get("product_id", "").strip()
    quantity = request.form.get("quantity", "").strip()

    if not all([customer_name, customer_email, product_id, quantity]):
        flash("Please complete every order field.", "danger")
        return redirect(url_for("storefront"))

    try:
        quantity_value = int(quantity)
        if quantity_value < 1:
            raise ValueError
    except ValueError:
        flash("Quantity must be a positive number.", "danger")
        return redirect(url_for("storefront"))

    db = get_db()
    product = db.execute(
        "select id, stock_status from products where id = %s", [product_id]
    ).fetchone()
    if product is None:
        flash("Selected product was not found.", "danger")
        return redirect(url_for("storefront"))
    if product["stock_status"] in {"Out of Stock", "Discontinued"}:
        flash("That product is currently unavailable.", "warning")
        return redirect(url_for("storefront"))

    db.execute(
        """
        insert into orders (customer_name, customer_email, product_id, quantity)
        values (%s, %s, %s, %s)
        """,
        [customer_name, customer_email, product_id, quantity_value],
    )
    db.commit()
    flash("Order received successfully.", "success")
    return redirect(url_for("storefront"))


@app.route("/manager-login", methods=["GET", "POST"])
def manager_login():
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == MANAGER_PASSWORD:
            session["manager_logged_in"] = True
            flash("Manager access granted.", "success")
            return redirect(url_for("manager_panel"))
        flash("Incorrect manager password.", "danger")
    return render_template("manager_login.html")


@app.post("/manager-logout")
def manager_logout():
    session.clear()
    flash("Signed out.", "info")
    return redirect(url_for("storefront"))


@app.get("/manager")
@manager_required
def manager_panel():
    db = get_db()
    products = db.execute(
        """
        select id, name, category, price, stock_status
        from products
        order by id desc
        """
    ).fetchall()
    orders = db.execute(
        """
        select orders.id, orders.customer_name, orders.customer_email,
               orders.quantity, orders.order_status, orders.created_at,
               products.name as product_name
        from orders
        join products on products.id = orders.product_id
        order by orders.id desc
        """
    ).fetchall()
    return render_template("manager.html", products=products, orders=orders)


@app.post("/manager/products")
@manager_required
def create_product():
    name = request.form.get("name", "").strip()
    category = request.form.get("category", "").strip()
    price = request.form.get("price", "").strip()
    stock_status = request.form.get("stock_status", "").strip()

    if not all([name, category, price, stock_status]):
        flash("All product fields are required.", "danger")
        return redirect(url_for("manager_panel"))

    try:
        price_value = float(price)
        if price_value < 0:
            raise ValueError
    except ValueError:
        flash("Price must be a positive number.", "danger")
        return redirect(url_for("manager_panel"))

    db = get_db()
    try:
        db.execute(
            """
            insert into products (name, category, price, stock_status)
            values (%s, %s, %s, %s)
            """,
            [name, category, price_value, stock_status],
        )
        db.commit()
        flash("Product created.", "success")
    except psycopg.errors.UniqueViolation:
        db.rollback()
        flash("A product with that name already exists.", "danger")

    return redirect(url_for("manager_panel"))


@app.post("/manager/products/<int:product_id>/edit")
@manager_required
def edit_product(product_id):
    name = request.form.get("name", "").strip()
    category = request.form.get("category", "").strip()
    price = request.form.get("price", "").strip()
    stock_status = request.form.get("stock_status", "").strip()

    try:
        price_value = float(price)
        if price_value < 0:
            raise ValueError
    except ValueError:
        flash("Price must be a positive number.", "danger")
        return redirect(url_for("manager_panel"))

    db = get_db()
    try:
        db.execute(
            """
            update products
            set name = %s, category = %s, price = %s, stock_status = %s
            where id = %s
            """,
            [name, category, price_value, stock_status, product_id],
        )
        db.commit()
        flash("Product updated.", "success")
    except psycopg.errors.UniqueViolation:
        db.rollback()
        flash("A product with that name already exists.", "danger")

    return redirect(url_for("manager_panel"))


@app.post("/manager/products/<int:product_id>/delete")
@manager_required
def delete_product(product_id):
    db = get_db()
    try:
        db.execute("delete from products where id = %s", [product_id])
        db.commit()
        flash("Product deleted.", "info")
    except psycopg.errors.ForeignKeyViolation:
        db.rollback()
        flash("Products with existing orders cannot be deleted.", "danger")
    return redirect(url_for("manager_panel"))


@app.post("/manager/orders/<int:order_id>/status")
@manager_required
def update_order_status(order_id):
    status = request.form.get("order_status", "").strip()
    if status not in product_choices()["order_statuses"]:
        flash("Invalid order status.", "danger")
        return redirect(url_for("manager_panel"))

    db = get_db()
    db.execute(
        "update orders set order_status = %s where id = %s",
        [status, order_id],
    )
    db.commit()
    flash("Order status updated.", "success")
    return redirect(url_for("manager_panel"))


init_db()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8000")), debug=True)
