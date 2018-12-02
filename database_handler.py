import pymysql
import time
import os
import sys
from datetime import datetime
import json

USERNAME = 'user1'
PASSWRD = '1234'
DB = 'investopedia'


def get_config():
    with open('config.txt') as f:
        config = json.loads(f.read())
    return config


def set_config(key, symbol):
    config = get_config()
    config[key] = symbol
    with open('config.txt', 'w') as f:
        f.write(json.dumps(config))


def create_db():
    """Creates the database"""
    con = pymysql.connect(user=USERNAME, password=PASSWRD)
    cur = con.cursor()
    cur.execute("CREATE DATABASE IF NOT EXISTS {} ;".format(DB))
    cur.execute("USE {};".format(DB))
    cur.execute("DROP TABLE IF EXISTS article_information ;")
    cur.execute("DROP TABLE IF EXISTS authors ;")
    cur.execute("DROP TABLE IF EXISTS categories ;")
    cur.execute("CREATE TABLE authors (id int AUTO_INCREMENT, name varchar(255) unique, PRIMARY KEY(id));")
    cur.execute("CREATE TABLE categories (id int AUTO_INCREMENT, name varchar(255) unique,  PRIMARY KEY(id));")
    cur.execute("""CREATE TABLE article_information 
    (id int AUTO_INCREMENT, 
    url varchar(1000) unique, 
    title varchar(255), 
    date DATETIME, 
    author_id int, 
    category_id int, 
    content TEXT, 

    PRIMARY KEY(id) 
     /* FOREIGN KEY (author_id) REFERENCES authors(id)
    FOREIGN KEY (category_id) REFERENCES categories(id) */
    );""")
    cur.execute("""ALTER TABLE article_information MODIFY content MEDIUMTEXT CHARACTER SET utf8;""")
    cur.execute("""CREATE TABLE stocks_prices
    (id int AUTO_INCREMENT,
    date TIMESTAMP,
    symbol varchar(255),
    open FLOAT,
    high FLOAT,
    low FLOAT,
    close FLOAT,
    volume FLOAT,
    
    PRIMARY KEY(id),
    UNIQUE KEY u_date_symbol (date, symbol))
    ;""")
    con.commit()
    con.close()


def insert_article_information(url, title, date, author, category, content):
    """Insert the article information into the database"""
    con = pymysql.connect(user=USERNAME, password=PASSWRD, db=DB)
    cur = con.cursor()
    try:
        author_id = cur.execute("INSERT INTO authors (name) VALUES (%s)", [author])
        con.commit()
    except pymysql.err.IntegrityError:
        # print("Already on the database - Author: {}.".format(author))
        cur.execute("Select id from authors where name = (%s)", [author])
        author_id = cur.fetchone()[0]

    try:
        category_id = cur.execute("INSERT INTO categories (name) VALUES (%s)", [category])
        con.commit()
    except pymysql.err.IntegrityError:
        # print("Already on the database - Category: {}.".format(category))
        cur.execute("Select id from categories where name = (%s)", category)
        category_id = cur.fetchone()[0]

    values = [url, title, date, author_id, category_id, content.text]

    already_parsed = False

    try:
        cur.execute(
            "INSERT INTO article_information (url, title, date, author_id, category_id, content) VALUES (%s, %s, %s, %s, %s, %s)",
            values)
        print(".", end="")
    except pymysql.err.IntegrityError:
        # print("Already on the database - URL: {}.".format(url))
        print(":", end="")
        already_parsed = True
    except pymysql.err.InternalError as e:
        try:
            print("2", end="")
            time.sleep(5)
            cur.execute(
                "INSERT INTO article_information (url, title, date, author_id, category_id, content) VALUES (%s, %s, %s, %s, %s, %s)",
                values)
            print(".", end="")
        except pymysql.err.InternalError as e:
            print("|", end="")
            with open(os.path.join(sys.path[0], "could_not_store_data.txt"), 'a') as f:
                f.write('{}\t{}\t{}\n'.format(datetime.now(), url, str(e)))
            already_parsed = True

    con.commit()
    con.close()
    return already_parsed


def insert_api(date, symbol, open_, high, low, close, volume):
    con = pymysql.connect(user=USERNAME, password=PASSWRD, db=DB)
    cur = con.cursor()
    already_inserted = False
    for _ in range(3):
        try:
            cur.execute(
                "INSERT INTO stocks_prices (date, symbol, open, high, low, close, volume) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                [date, symbol, open_, high, low, close, volume])
            break
        except pymysql.err.IntegrityError:
            print(":", end="")
            already_inserted = True
            break
        except pymysql.err.InternalError as e:
            print("5", e)
            time.sleep(5)

    con.commit()
    con.close()

    return already_inserted
