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
import multiprocessing
from functools import partial


BASE_URL = "https://www.investopedia.com"
VISITED_URLS = set()

USERNAME = 'root'
PASSWRD = 'sqlvaldo'
DB = 'investopedia'


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
    cur.execute("""ALTER TABLE article_information MODIFY content MEDIUMTEXT CHARACTER SET utf8;""")
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
        except TimeoutError as e:
            print('Not succesful in the {} try.'.format(tries))
            time.sleep(15)
            print(e)
            sys.exit()
        except Exception as e:
            print(e)
        print("Tries: {}".format(tries))

    soup = BeautifulSoup(r.text, 'lxml')
    if not r.ok:
        return None
    return soup


def insert_db(url, title, date, author, category, content):
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
    try:
        cur.execute(
            "INSERT INTO article_information (url, title, date, author_id, category_id, content) VALUES (%s, %s, %s, %s, %s, %s)",
            values)
        print(".", end="")
    except pymysql.err.IntegrityError:
        # print("Already on the database - URL: {}.".format(url))
        print(":", end="")
    except pymysql.err.InternalError as e:
        try:
            print("2", end="")
            time.sleep(5)
            cur.execute(
                "INSERT INTO article_information (url, title, date, author_id, category_id, content) VALUES (%s, %s, %s, %s, %s, %s)",
                values)
            print(".", end="")
        except pymysql.err.InternalError as e:
            print("|",end="")
            with open(os.path.join(sys.path[0], "could_not_store_data.txt"), 'a') as f:
                f.write('{}\t{}\t{}\n'.format(datetime.now(), url, str(e)))
    con.commit()
    con.close()


def parse_page_information(url, title, date, author, content, describe):
    """Prints (for now) the article information in the page depending on the parameters given."""
    soup = url_to_soup(url)

    if not soup:
        return

    article_category = soup.find('meta', {'property': 'emailprimarychannel'})
    if article_category:
        article_category = article_category['content']
    else:
        article_category = soup.find('meta', {'property': "emailprimarysubchannel"})
        if article_category:
            article_category = article_category['content']

    article_title = soup.find('h1')
    if article_title:
        article_title = article_title.text.strip()

    article_date = soup.find('meta', {'property': "article:published_time"})
    if article_date:
        article_date = soup.find('meta', {'property': "article:published_time"})['content']

    article_author = soup.find('meta', {'name': 'author'})
    if article_author:
        article_author = article_author['content']

    article_content = soup.find('div', {'class': 'content-box'})
    if not article_content:
        print("!",end="")
        article_content = soup.find('div', {'class': 'roth__content'})

    # check if everything has value
    if not article_category:
        with open(os.path.join(sys.path[0], "could_not_store_data.txt"), 'a') as f:
            f.write('{}\t{}\t{}\n'.format(datetime.now(), url, "Category was None"))
        return
    if not article_author:
        with open(os.path.join(sys.path[0], "could_not_store_data.txt"), 'a') as f:
            f.write('{}\t{}\t{}\n'.format(datetime.now(), url, "Author was None"))
        return
    if not article_content:
        with open(os.path.join(sys.path[0], "could_not_store_data.txt"), 'a') as f:
            f.write('{}\t{}\t{}\n'.format(datetime.now(), url, "Content was None"))
        return
    if not article_date:
        with open(os.path.join(sys.path[0], "could_not_store_data.txt"), 'a') as f:
            f.write('{}\t{}\t{}\n'.format(datetime.now(), url, "Date was None"))
        return
    if not article_title:
        with open(os.path.join(sys.path[0], "could_not_store_data.txt"), 'a') as f:
            f.write('{}\t{}\t{}\n'.format(datetime.now(), url, "Title was None"))
        return

    article_category = article_category.lower()
    article_date = datetime.strptime(article_date.rsplit('-', 1)[0], r"%Y-%m-%dT%H:%M:%S")

    insert_db(url, article_title, article_date, article_author, article_category, article_content)

    if describe:
        title = True
        date = True
        author = True
        content = True

    # print("-" * 40)
    # print('URL: {url}'.format(url=url))
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


def get_urls(soup):
    h3 = soup.find_all('h3')

    hrefs = [tag.find('a', {"href": True})['href'] for tag in h3]
    urls = [BASE_URL + href for href in hrefs if not href.startswith(r'/ask')]

    return urls


def run_scrape_indexes_pages(title, date, author, content, describe):
    """Scrape articles iterating from the index pages"""
    try:
        with open(os.path.join(sys.path[0], "position_scraping.txt")) as f:
            index_page, page_num = f.read().splitlines()
    except FileNotFoundError:
        page_num = 0
        index_page = 'https://www.investopedia.com/news/'

    with open(os.path.join(sys.path[0], "index_pages.txt")) as f:
        index_pages = f.read().splitlines()

    # Loop in the index pages listed in index_pages.txt file
    for index_page in index_pages[index_pages.index(index_page):]:

        soup = url_to_soup("{index_page}?page={page_num}".format(index_page=index_page, page_num=0))

        # Get the number os pages
        last_page_href = soup.find("li", {"class": "pager-last last"}).a["href"]
        last_page_num = int(re.findall(r"page=(\d+)", last_page_href)[0])

        # For each page scrape the content for each article
        for page_num in range(int(page_num), last_page_num + 1):
            soup = url_to_soup("{index_page}?page={page_num}".format(index_page=index_page, page_num=page_num))

            print("\n-------------- Page: {} of {} --------------".format(page_num, last_page_num))
            urls = get_urls(soup)

            ##for debugging:
            # for url in urls:
            #     parse_page_information( title = title, author = author, date = date, content = content, describe = describe, url=url)

            with multiprocessing.Pool(10) as pool:
                pool.map(partial(parse_page_information, title=title, author=author, date=date, content=content, describe=describe), urls)
                #parse_page_information(url, title, date, author, content, describe)

            # Save the page you are in
            with open(os.path.join(sys.path[0], "position_scraping.txt"), 'w') as f:
                f.write("{}\n{}".format(index_page, int(page_num) + 1))
        page_num = 0

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
