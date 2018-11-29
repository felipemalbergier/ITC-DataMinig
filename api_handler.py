import requests
import json
import pandas as pd
import database_handler
import os
import sys
import multiprocessing

BASE_API_URL = "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={}&outputsize=full&apikey=MVDRMN0YX4UJ0D1I"


def get_stock_symbols():
    with open(os.path.join(sys.path[0], 'stock_symbols.txt')) as f:
        stock_symbols = f.read()
    stock_symbols = stock_symbols.splitlines()
    stock_symbols = [l.rsplit(" ", 2)[1] for l in stock_symbols]
    print("Fetching 3 stocks only")
    return stock_symbols[:2]


def manipulate_data(stock_price):
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
    stock_symbols = get_stock_symbols()

    # stock_prices = []
    # for stock_symbol in stock_symbols:
    #     r = requests.get(BASE_API_URL.format(stock_symbol[1]))
    #     stock_prices.append(json.loads(r.text))

    with multiprocessing.Pool(14) as pool:
        stock_prices = pool.map(fetch_api_info, stock_symbols)

    for stock_price in stock_prices:

        df = manipulate_data(stock_price)
        if new_information:
            df = df.iloc[::-1]

        for row in df.values:
            date, symbol, open_, high, low, close, volume = row
            print(row)
            already_inserted = database_handler.insert_api(str(date), symbol, open_, high, low, close, volume)

            if already_inserted and new_information:
                break
