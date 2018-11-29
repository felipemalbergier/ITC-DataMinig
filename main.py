#!/usr/bin/env python
"""
This is a Web Scraper that crawls investopedia.com fetching articles.
It is a project at ITC - Israel Tech Challange Program.

Authors: Felipe Malbergier and Shalom Azar
"""

import click
import scrapper_handler
import api_handler

# import database


@click.command()
@click.option('--new_information', is_flag=True, help="Activate this flag to scrape only new articles.")
@click.option('--api', is_flag=True, help="Activate this flag to pull new information of the api.")
def main(new_information, api):
    # database.create_db()
    if api:
        api_handler.get_stock_prices(new_information)
        pass
    else:
        scrapper_handler.get_article_information(new_information)


if __name__ == "__main__":
    main()
