import requests
from bs4 import BeautifulSoup
import re
import click

BASE_URL = "https://www.investopedia.com"
NEWS_URL = r'/news/?page={}'
VISITED_URLS = set()


def url_to_soup(url):
    """Returns a soup object from the 'url' given."""
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'lxml')
    return soup


def parse_page_information(url, title, date, author, content, describe):
    """Prints (for now) the article information in the page."""
    soup_news = url_to_soup(url)
    
    title_string = soup_news.find('h1').text.strip()
    date_string = soup_news.find('meta', {'property': "article:published_time"})['content']
    author_string = soup_news.find('span', {'class': 'by-author'}).a.text
    content_string = soup_news.find('div', {'class': 'content-box'})

    if describe:
        title = True
        date = True
        author = True
        content = True

    print("-"*40)
    print('URL: {url}'.format(url=url))
    if title:
        print('Title: {title}'.format(title=title_string))
    if date:
        print('Date: {date}'.format(date=date_string))
    if author:
        print('Author: {author}'.format(author=author_string))
    if content:
        print('Len of Content: {len_content}'.format(len_content=len(content_string.text)))


def get_list_href(url):
    soup = url_to_soup(url)
    hrefs = soup.find_all('', {'href': True})
    hrefs = [BASE_URL + u['href'] for u in hrefs if re.match(r'/[^/]', u['href'])]
    return hrefs


@click.command()
@click.option('--title', is_flag=True)
@click.option('--date', is_flag=True)
@click.option('--author', is_flag=True)
@click.option('--content', is_flag=True)
@click.option('--describe', is_flag=True)
def main(title, date, author, content, describe):
    URLS_TO_VISIT = []
    URLS_TO_VISIT.append(BASE_URL)

    while len(URLS_TO_VISIT) > 0:

        url_to_visit = URLS_TO_VISIT.pop(0)
        while url_to_visit in VISITED_URLS:
            url_to_visit = URLS_TO_VISIT.pop(0)

        #print(url_to_visit + '\r')

        try:
            parse_page_information(url_to_visit, title, date, author, content, describe)
        except AttributeError:
            print('.')
        except TypeError:
            print('.')
        news_href = get_list_href(url_to_visit)
        URLS_TO_VISIT += news_href

        VISITED_URLS.add(url_to_visit)



if __name__ == "__main__":
    main()


"""
Indexes pages:
- https://www.investopedia.com/news/
- https://www.investopedia.com/investing/mutual-funds/news/
- https://www.investopedia.com/investing/mutual-funds/education/
- https://www.investopedia.com/investing/investing-basics/education/
- https://www.investopedia.com/investing/investing-basics/strategy/
- https://www.investopedia.com/tech/robo-advisor/
- 
- 

"""