import requests
from bs4 import BeautifulSoup
import multiprocessing
from functools import partial
import re
from fake_useragent import UserAgent
import time
import sys
import os
from datetime import datetime
import database_handler

BASE_URL = "https://www.investopedia.com"


def get_urls(soup):
    h3 = soup.find_all('h3')

    hrefs = [tag.find('a', {"href": True})['href'] for tag in h3]
    urls = [BASE_URL + href for href in hrefs]  # if not href.startswith(r'/ask')]

    return urls


def url_to_soup(url):
    """Returns a soup object from the 'url' given."""
    headers = {
        'User-Agent': UserAgent(verify_ssl=False).random,
        'From': 'youremail@domain.com'  # This is another valid field
    }
    for tries in range(5):
        try:
            r = requests.get(url, timeout=60, headers=headers)
            break
        except TimeoutError as e:
            print('Not successful in the {} try.'.format(tries))
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


def parse_page_information(url):
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
        print("!", end="")
        article_content = soup.find('div', {'class': 'roth__content'})
        if not article_content:
            print("@", end="")
            article_content = soup.find('div', {'class': 'fa-question'})

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

    already_parsed = database_handler.insert_article_information(url, article_title, article_date, article_author, article_category,
                                                                 article_content)

    return already_parsed


def get_article_information(new_information):
    """Scrape articles iterating from the index pages"""

    with open(os.path.join(sys.path[0], "position_scraping.txt")) as f:
        index_page, page_num = f.read().splitlines()

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

            # ##for debugging:
            # for url in urls:
            #     parse_page_information(url=url)

            with multiprocessing.Pool(14) as pool:
                already_parsed_pages = pool.map(parse_page_information, urls)
            if all(already_parsed_pages) and new_information:
                break

            # Save the page you are in
            with open(os.path.join(sys.path[0], "position_scraping.txt"), 'w') as f:
                f.write("{}\n{}".format(index_page, int(page_num) + 1))
        page_num = 0
