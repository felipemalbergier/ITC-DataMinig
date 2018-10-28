import requests
from bs4 import BeautifulSoup


BASE_URL = "https://www.investopedia.com"
NEWS_URL = r'/news/?page={}'

def url_to_soup(url):
    """Returns a soup object from the 'url' given."""
    r = requests.get(url)
    soup = BeautifulSoup(r.text,'lxml')
    return soup


def parse_page_information(url):
    """Prints (for now) the article information in the page."""
    soup_news = url_to_soup(url)
    
    title = soup_news.find('h1').text.strip()
    date = soup_news.find('meta', {'property':"article:published_time"})['content']
    author = soup_news.find('span', {'class':'by-author'}).a.text
    content = soup_news.find('div', {'class':'content-box'})
    
    print('''------------------------------------------------------------------------
    URL: {url}
    Title: {title}
    Date: {date}
    Author: {author}
    Len of Content: {len_content}
    '''.format(url=url, title=title, date=date, author=author, len_content=len(content.text)))


def main():
    for index in range(50):
        soup = url_to_soup(BASE_URL+NEWS_URL.format(index))
        
        h3 = soup.find_all('h3')
        for tag in h3:
            href = tag.find('a',{"href":True})['href']
            if not href.startswith(r'/ask'):
                url = BASE_URL + href
                parse_page_information(url)


if __name__ == "__main__":
    main()