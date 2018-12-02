import requests
import json
import pandas as pd
import database_handler
import os
import sys
import time

BASE_API_URL = "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={}&outputsize=full&apikey=MVDRMN0YX4UJ0D1I"


def get_stock_symbols():
    with open(os.path.join(sys.path[0], 'stock_symbols.txt')) as f:
        stock_symbols = f.read()
    stock_symbols = stock_symbols.splitlines()
    stock_symbols = [l.rsplit(" ", 2)[1] for l in stock_symbols]
    # print("Fetching 3 stocks only")
    return stock_symbols


def manipulate_data(stock_price):
    if "Error Message" in stock_price.keys() or "Note" in stock_price.keys():
        # Log error message
        return pd.DataFrame([])

    symbol = stock_price['Meta Data']['2. Symbol']
    prices = stock_price['Time Series (Daily)']
    df = pd.read_json(json.dumps(prices))
    df = df.transpose()
    df = df.reset_index()
    df.insert(1, 'symbol', [symbol] * df.shape[0])
    df = df.rename_axis(
        {"index": "date", "1. open": 'open', '2. high': 'high', '3. low': 'low', "4. close": "close",
         "5. volume": 'volume'}, axis=1)
    return df


def fetch_api_info(stock_symbol):
    r = requests.get(BASE_API_URL.format(stock_symbol))
    return json.loads(r.text)


def get_stock_prices(new_information):
    ast_stock_scraped = database_handler.get_config()['api_position']
    stock_symbols = get_stock_symbols()

    for stock_to_scrape in stock_symbols[stock_symbols.index(ast_stock_scraped) + 1:]:
        print("\n" + stock_to_scrape)
        stock_prices = fetch_api_info(stock_to_scrape)

        df = manipulate_data(stock_prices)
        if new_information:
            df = df.iloc[::-1]

        for row in df.values:
            date, symbol, open_, high, low, close, volume = row
            already_inserted = database_handler.insert_api(str(date), symbol, open_, high, low, close, volume)
            print(".", end="")
            if already_inserted and new_information:
                break

        database_handler.set_config('api_position', stock_to_scrape)
        time.sleep(13)
