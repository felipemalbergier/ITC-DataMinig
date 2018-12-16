# coding: utf-8

# # STOP WORDS

from nltk.corpus import stopwords
from nltk import word_tokenize
import database_handler as db_handler
import pymysql
import os
import sys
import re


def get_stock_symbols():
    with open(os.path.join(sys.path[0], 'stock_symbols.txt')) as f:
        stock_symbols = f.read()
    stock_symbols = stock_symbols.splitlines()
    stock_symbols = [l.rsplit(" ", 2)[1] for l in stock_symbols]
    # print("Fetching 3 stocks only")
    return stock_symbols


IGNORED_SYMBOLS = ["&", "#"]
STOCK_SYMBOLS = get_stock_symbols()
ENGLISH_STOPWORDS = stopwords.words('english')


def rejoin_possible_tokens(tokens):
    i_offset = 0
    for i, t in enumerate(tokens):
        i -= i_offset
        if (t in IGNORED_SYMBOLS or tokens[i - 1][-1] in IGNORED_SYMBOLS) and i > 0:
            left = tokens[:i - 1]
            joined = [tokens[i - 1] + t]
            right = tokens[i + 1:]
            tokens = left + joined + right
            i_offset += 1
    return tokens


# ## TOKENIZE AND STOCKS MENTIONED


def get_stoks_and_tokens(text):
    word_tokens = word_tokenize(text)
    word_tokens = rejoin_possible_tokens(word_tokens)
    possible_stock_symbols = list(filter(lambda w: re.match(r"^[A-Z0-9]+$", w) and w in STOCK_SYMBOLS, word_tokens))
    # remove punctiation and number and lower case the words
    word_tokens = [word.lower()
                   for word in word_tokens if
                   not re.match(r"^\W+$|^\d+\W*\d*$|'\w+", word) and word not in ENGLISH_STOPWORDS]

    return word_tokens, possible_stock_symbols


# ## GENERATOR QUERY

def run_query_gen(query):
    con = pymysql.connect(user=db_handler.USERNAME, password=db_handler.PASSWRD, db=db_handler.DB)
    cur = con.cursor()
    cur.execute(query)
    con.commit()
    while cur:
        one = cur.fetchone()
        yield one
    con.close()


def run_query(query, list_to_insert):
    con = pymysql.connect(user=db_handler.USERNAME, password=db_handler.PASSWRD, db=db_handler.DB)
    cur = con.cursor()
    cur.execute(query, list_to_insert)
    con.commit()
    con.close()


def main():
    query = "select id, title, content from article_information"
    title_and_content = run_query_gen(query)
    # title_and_content = [
    #     [1, 'title title a on in felipe', 'and for a case in real time of football scraper in the streets']]
    # # MANIPULATE AND INSERT ON DB
    # Important to notice that I've filtered the stocks with the ones that we could scrape.

    for i, row in enumerate(title_and_content):
        ide = row[0]
        title_tokens, title_stocks = get_stoks_and_tokens(row[1])
        article_tokens, article_stocks = get_stoks_and_tokens(row[2])

        query = """INSERT INTO manipulated_data (id, tokenized_title, stocks_mentioned_title, tokenized_article, stocks_mentioned_article) VALUES (%s, %s, %s, %s, %s)"""
        run_query(query,
                  [ide, r" ".join(title_tokens), r" ".join(title_stocks), r" ".join(article_tokens),
                   r" ".join(article_stocks)])
        # print(query)
        # print([ide, r" ".join(title_tokens), r" ".join(title_stocks), r" ".join(article_tokens),
        #        r" ".join(article_stocks)])
        # print(title_and_content)
        if i % 500 == 0:
            print("{}/48,159".format(i), end="\r")


if __name__ == '__main__':
    main()
