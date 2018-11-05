import sqlite3

con = sqlite3.connect('investopedia_data.db')
cur = con.cursor()
cur.execute("CREATE TABLE article_information (url TEXT, title varchar(255), date DATETIME, author_id int, category_id int)")