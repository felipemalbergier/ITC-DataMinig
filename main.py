#!/usr/bin/env python
"""
This is a Web Scraper that crawls investopedia.com fetching articles.
It is a project at ITC - Israel Tech Challange Program.

Authors: Felipe Malbergier and Shalom Azar
"""
import requests
from bs4 import BeautifulSoup
import re
import click
import os
from datetime import datetime

BASE_URL = "https://www.investopedia.com"
VISITED_URLS = set()
URLS_TO_VISIT = []


def url_to_soup(url):
    """Returns a soup object from the 'url' given."""
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'lxml')
    return soup


def parse_page_information(url, title, date, author, content, describe):
    """Prints (for now) the article information in the page depending on the parameters given."""
    soup_news = url_to_soup(url)

    article_title = soup_news.find('h1').text.strip()
    article_date = soup_news.find('meta', {'property': "article:published_time"})['content']
    article_date = datetime.strptime(article_date, r"%Y-%m-%dT%H:%M:%S")
    article_author = soup_news.find('span', {'class': 'by-author'}).a.text
    article_content = soup_news.find('div', {'class': 'content-box'})

    if describe:
        title = True
        date = True
        author = True
        content = True

    print("-" * 40)
    print('URL: {url}'.format(url=url))
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
    with open(os.path.join("C:\\Users\\Felipe\\OneDrive\\Python\\ITC-DataMining", "index_pages.txt")) as f:
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
    if scrape_whole_website:
        run_scrape_whole_website(title, date, author, content, describe)
    else:
        run_scrape_indexes_pages(title, date, author, content, describe)


if __name__ == "__main__":
    main()