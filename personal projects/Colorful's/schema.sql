DROP TABLE IF EXISTS products;
CREATE TABLE products
(
    product_id INTEGER PRIMARY KEY AUTOINCREMENT, 
    name TEXT NOT NULL,
    price REAL NOT NULL, 
    image_filename TEXT,
    quantity INTEGER NOT NULL DEFAULT 0,
    description TEXT
);

INSERT INTO products (name, price, image_filename, quantity, description) 
VALUES
('Rose',7.99,'rose.jpg',20,'A classic red rose, perfect for romance.'), 
('Tulip',5.50,'tulip.jpg',25,'Vibrant spring tulip.'), 
('Lily',4.00,'lily.jpg',15,'Elegant white lily.'), 
('Sunflower',6.25,'sunflower.jpg',18,'Tall and cheerful sunflower.'), 
('Daisy',3.75,'daisy.jpg',30,'Simple and charming daisy.'), 
('Orchid',10.00,'orchid.jpg',10,'Exotic pink orchid.');


DROP TABLE IF EXISTS users;
CREATE TABLE users
(
    user_id TEXT PRIMARY KEY,
    password TEXT NOT NULL,
    admin_status BOOLEAN NOT NULL,
    points_balance INTEGER NOT NULL DEFAULT 0
);

INSERT INTO users(user_id, password, admin_status)
VALUES
('admin', '123', TRUE);

DROP TABLE IF EXISTS favourites;
CREATE TABLE favourites
(
    user_id    TEXT    NOT NULL,
    product_id INTEGER NOT NULL,
    PRIMARY KEY (user_id, product_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
CREATE TABLE orders
(
    order_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    TEXT    NOT NULL,
    order_date TEXT    NOT NULL,
    address    TEXT    NOT NULL,
    city       TEXT    NOT NULL,
    postal_code TEXT   NOT NULL,
    country    TEXT    NOT NULL,
    status     TEXT    NOT NULL DEFAULT 'active',
    admin_note TEXT,
    points_used INTEGER NOT NULL DEFAULT 0,
    points_earned INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE order_items
(
    order_id   INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity   INTEGER NOT NULL,
    unit_price REAL    NOT NULL,
    PRIMARY KEY (order_id, product_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

DROP TABLE IF EXISTS reviews;
CREATE TABLE reviews
(
    review_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id   INTEGER NOT NULL,
    user_id    TEXT    NOT NULL,
    rating     INTEGER NOT NULL,
    comment    TEXT,
    created_at TEXT    NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (user_id)  REFERENCES users(user_id)
);