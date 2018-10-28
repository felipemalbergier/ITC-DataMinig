import requests
from bs4 import BeautifulSoup

URL = "https://www.investopedia.com/news/?page=0"


'https://www.investopedia.com/articles/basics/'
'https://www.investopedia.com/articles/pf/'
"https://www.investopedia.com/articles/trading/"
"https://www.investopedia.com/articles/forex/"


'''
Title   -> h1
Author  -> span class="by author"
Date    -> meta property="article:published_time" content=DATE"
Text    -> div class="content-box"
Categorie -> URL
'''
'''
h3 Goes to index 49 
Do a logic that scrapes the index untill it get less than 7 articles.
'''
