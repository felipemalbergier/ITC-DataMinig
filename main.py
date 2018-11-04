import requests
from bs4 import BeautifulSoup
import re

BASE_URL = "https://www.investopedia.com"
NEWS_URL = r'/news/?page={}'
VISITED_URLS = set()


def url_to_soup(url):
    """Returns a soup object from the 'url' given."""
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'lxml')
    return soup


def parse_page_information(url):
    """Prints (for now) the article information in the page."""
    soup_news = url_to_soup(url)
    
    title = soup_news.find('h1').text.strip()
    date = soup_news.find('meta', {'property': "article:published_time"})['content']
    author = soup_news.find('span', {'class':'by-author'}).a.text
    content = soup_news.find('div', {'class':'content-box'})
    
    print('''
    URL: {url}
    Title: {title}
    Date: {date}
    Author: {author}
    Len of Content: {len_content}
    '''.format(url=url, title=title, date=date, author=author, len_content=len(content.text)))


def get_list_href(url):
    soup = url_to_soup(url)
    hrefs = soup.find_all('', {'href': True})
    hrefs = [BASE_URL + u['href'] for u in hrefs if re.match(r'/[^/]', u['href'])]
    return hrefs


def main():
    URLS_TO_VISIT = []
    URLS_TO_VISIT.append(BASE_URL)

    while len(URLS_TO_VISIT) > 0:

        url_to_visit = URLS_TO_VISIT.pop(0)
        while url_to_visit in VISITED_URLS:
            url_to_visit = URLS_TO_VISIT.pop(0)

        print(url_to_visit + '\r', end="")

        try:
            parse_page_information(url_to_visit)
        except AttributeError:
            print('.', end='')
        except TypeError:
            print('.', end='')
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