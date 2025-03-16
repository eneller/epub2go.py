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
    converter = GBConvert('./')
    for book in tqdm(books):
        if book.url is not None:
            converter.download(book.url)


if __name__ == "__main__":
    main()
