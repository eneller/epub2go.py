import requests
from tqdm import tqdm
from bs4 import BeautifulSoup
from bs4 import ResultSet

import os
from urllib.parse import urljoin

from convert import GBConvert, allbooks_url, get_all_books, Book

def main():
    books = get_all_books()
    # NOTE consider making this a map()
    for book in tqdm(books):
        if book.url is not None:
            GBConvert(book.url).run()


if __name__ == "__main__":
    main()
