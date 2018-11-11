#!/usr/bin/env python
"""
This is a Web Scraper that crawls investopedia.com fetching articles.
It is a project at ITC - Israel Tech Challange Program.

Authors: Felipe Malbergier and Shalom Azar
"""
import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import re
import click
import os
from datetime import datetime
import pymysql
import sys
import time

BASE_URL = "https://www.investopedia.com"
VISITED_URLS = set()

USERNAME = 'root'
PASSWRD = 'sqlvaldo'
DB ='investopedia'


def create_db():
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
    con.commit()
    con.close()


def url_to_soup(url):
    """Returns a soup object from the 'url' given."""
    headers = {
        'User-Agent': UserAgent().random,
        'From': 'youremail@domain.com'  # This is another valid field
    }
    for tries in range(5):
        try:
            r = requests.get(url, timeout=60, headers=headers)
            break
        except TimeoutError:
            print('Not succesful in the {} try.'.format(tries))
            time.sleep(15)
    soup = BeautifulSoup(r.text, 'lxml')
    return soup


def insert_db(url, title, date, author, category, content):
    con = pymysql.connect(user=USERNAME, password=PASSWRD, db=DB)
    cur = con.cursor()
    try:
        author_id = cur.execute("INSERT INTO authors (name) VALUES (%s)", [author])
        con.commit()
    except pymysql.err.IntegrityError:
        print("Author: {} already on the database.".format(author))
        cur.execute("Select id from authors where name = (%s)", [author])
        author_id = cur.fetchone()[0]

    try:
        category_id = cur.execute("INSERT INTO categories (name) VALUES (%s)", [category])
        con.commit()
    except pymysql.err.IntegrityError:
        print("Category: {} already on the database.".format(category))
        cur.execute("Select id from categories where name = (%s)", category)
        category_id = cur.fetchone()[0]

    values = [url, title, date, author_id, category_id, content.text]
    try:
        cur.execute("INSERT INTO article_information (url, title, date, author_id, category_id, content) VALUES (%s, %s, %s, %s, %s, %s)", values)
    except pymysql.err.IntegrityError:
        print("URL: {} already on the database".format(url))
    con.commit()
    con.close()


def parse_page_information(url, title, date, author, content, describe):
    """Prints (for now) the article information in the page depending on the parameters given."""
    soup = url_to_soup(url)

    article_category = soup.find('meta', {'property': 'emailprimarychannel'})['content']
    article_category = article_category.lower()
    article_title = soup.find('h1').text.strip()
    article_date = soup.find('meta', {'property': "article:published_time"})['content']
    article_date = datetime.strptime(article_date.rsplit('-', 1)[0], r"%Y-%m-%dT%H:%M:%S")
    article_author = soup.find('span', {'class': 'by-author'}).a.text
    article_content = soup.find('div', {'class': 'content-box'})

    insert_db(url, article_title, article_date, article_author, article_category, article_content)

    if describe:
        title = True
        date = True
        author = True
        content = True

    print("-" * 40)
    print('URL: {url}'.format(url=url))
    print('Category: {categorystring}'.format(categorystring=article_category))
    if title:
        print('Title: {title}'.format(title=article_title))
    if date:
        print('Date: {date}'.format(date=article_date))
    if author:
        print('Author: {author}'.format(author=article_author))
    if content:
        print('Len of Content: {len_content}'.format(len_content=len(article_content.text)))


def get_list_href(url):
    """Returns a list of hrefs links fond on the 'url'. It also concatenate the href with the base url."""
    soup = url_to_soup(url)
    hrefs = soup.find_all('', {'href': True})
    hrefs = [BASE_URL + u['href'] for u in hrefs if re.match(r'/[^/]', u['href'])]
    return hrefs


def run_scrape_whole_website(title, date, author, content, describe):
    """Starts scraping the whole website from the main URL."""
    URLS_TO_VISIT = []
    URLS_TO_VISIT.append(BASE_URL)

    while len(URLS_TO_VISIT) > 0:

        url_to_visit = URLS_TO_VISIT.pop(0)
        while url_to_visit in VISITED_URLS:
            url_to_visit = URLS_TO_VISIT.pop(0)

        # print(url_to_visit + '\r')

        try:
            parse_page_information(url_to_visit, title, date, author, content, describe)
        except AttributeError:
            print('.')
        except TypeError:
            print('.')
        news_href = get_list_href(url_to_visit)
        URLS_TO_VISIT += news_href

        VISITED_URLS.add(url_to_visit)


def run_scrape_indexes_pages(title, date, author, content, describe):
    """Scrape articles iterating from the index pages"""
    with open(os.path.join(sys.path[0], "index_pages.txt")) as f:
        index_pages = f.read().splitlines()

    # Loop in the index pages listed in index_pages.txt file
    for index_page in index_pages:
        soup = url_to_soup("{index_page}?page={page_num}".format(index_page=index_page, page_num=0))

        # Get the number os pages
        last_page_href = soup.find("li", {"class": "pager-last last"}).a["href"]
        last_page_num = int(re.findall(r"page=(\d+)", last_page_href)[0])

        # For each page scrape the content for each article
        for page_num in range(last_page_num):
            soup = url_to_soup("{index_page}?page={page_num}".format(index_page=index_page, page_num=page_num))

            h3 = soup.find_all('h3')
            for tag in h3:
                href = tag.find('a', {"href": True})['href']
                if not href.startswith(r'/ask'):
                    url = BASE_URL + href
                    parse_page_information(url, title, date, author, content, describe)


@click.command()
@click.option('--title', is_flag=True)
@click.option('--date', is_flag=True)
@click.option('--author', is_flag=True)
@click.option('--content', is_flag=True)
@click.option('--describe', is_flag=True)
@click.option('--scrape_whole_website', is_flag=True)
def main(title, date, author, content, describe, scrape_whole_website=False):
    # create_db()
    if scrape_whole_website:
        run_scrape_whole_website(title, date, author, content, describe)
    else:
        run_scrape_indexes_pages(title, date, author, content, describe)


if __name__ == "__main__":
    main()