import mysql.connector


def connect_to_database():
    connector = mysql.connector.connect(host='localhost', database='investopedia_data.db', password='felipeshalom')
    return connector

def create_database():
    connector = connect_to_database()
    connector.execute("DROP TABLE article_information")
    connector.execute("DROP TABLE authors")
    connector.execute("DROP TABLE categories")
    connector.execute(
        """CREATE TABLE article_information (ID int AUTO_INCREMENT, url TEXT, title varchar(255), date varchar(255), author_id int, category_id int, content TEXT, PRIMARY KEY(ID))")
    connector.execute("CREATE TABLE authors (ID int AUTO_INCREMENT, name varchar(255) unique, PRIMARY KEY(ID))")
    connector.execute("CREATE TABLE categories (ID int AUTO_INCREMENT, name varchar(255) unique,  PRIMARY KEY(ID))")
    connector.commit()


def main():
    create_database()












if __name__ == '__main__':
    main()

