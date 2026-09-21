# Flower Shop Flask App

This folder contains a Flask flower-shop web application. It supports user registration and login, browsing products, a shopping cart, checkout, favourites, orders, reviews, points, and administrator management pages.

## 1. Requirements

You need:

- macOS or another operating system with Python 3
- Python 3.10 or newer recommended
- A terminal
- `sqlite3` (already included with macOS)

## 2. Open the project in Terminal

Open the project in integrated terminal.

## 3. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 4. Install the dependencies

```bash
python3 -m pip install --upgrade pip
python3 -m pip install Flask Flask-Session Flask-WTF Werkzeug
```

## 5. Check the database

An `app.db` file is already included, so you can normally start the application without creating a database.

The included database contains an administrator account:

```text
Username: admin
Password: 123
```

## 6. Start the development server

```bash
python3 -m flask --app app run
```

Flask will print a local address, normally:

```text
http://127.0.0.1:5000
```

Open that address in your browser.

To stop the server, return to the terminal and press `Ctrl+C`.

## 7. Try the application

### As a normal user

1. Open `/auth`, or use the login/register link in the navigation.
2. Register a new account.
3. Open the products page and add products to the cart.
4. Open the cart and continue to checkout.
5. Enter an address, city, postal code, and country.
6. Place the order.
7. Visit the account or orders pages to view account information and orders.
8. Use favourites and leave a review after completing an order.

Useful pages:

- `/` - home page
- `/products` - all products
- `/auth` - login and registration
- `/cart` - shopping cart
- `/checkout` - checkout
- `/favorites` - favourite products
- `/orders` - current user's orders
- `/account` - account settings
- `/logout` - log out

### As an administrator

1. Log in with `admin` / `123`.
2. Open `/admin` or use the admin link in the navigation.
3. Manage products, quantities, users, orders, order notes, and reviews.

Administrator pages include:

- `/admin` - administrator dashboard
- `/admin/products` - add, update, and delete products
- `/admin/orders_and_users` - manage orders and users
- `/admin/reviews` - manage reviews

## 8. Reset the database

`schema.sql` drops and recreates the tables and restores the sample products and admin account. This permanently deletes users, orders, favourites, and reviews stored in the current database.

Stop the Flask server first, then run this command:

```bash
sqlite3 app.db < schema.sql
```

Then start the server again.

## Important files

- `app.py` - Flask routes and application logic
- `database.py` - SQLite connection setup
- `forms.py` - login, registration, checkout, account, and product forms
- `schema.sql` - database structure and sample data
- `app.db` - current SQLite database
- `templates/` - HTML pages
- `static/` - CSS, JavaScript, and image files
- `run.py` - CGI entry point for a compatible web server; it is not the recommended command for local development
