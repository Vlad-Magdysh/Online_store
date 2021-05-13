CREATE TABLE users (
    email TEXT PRIMARY KEY ,
    password TEXT NOT NULL ,
    phone TEXT NOT NULL ,
    name TEXT NOT NULL ,
    surname TEXT NOT NULL ,
    city TEXT NOT NULL ,
    mail_index INTEGER NOT NULL
);

CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    name TEXT NOT NULL,
    quantity INTEGER,
    country TEXT NOT NULL,
    description TEXT
);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT NOT NULL ,
    description TEXT ,
    status INTEGER
);

CREATE TABLE letters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_name TEXT NOT NULL ,
    user_phone TEXT NOT NULL ,
    user_email TEXT NOT NULL ,
    description TEXT ,
    status INTEGER
);