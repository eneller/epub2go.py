import requests
from tqdm import tqdm
from bs4 import BeautifulSoup
from bs4 import ResultSet

import os
from urllib.parse import urljoin

from convert import GBConvert, allbooks_url, get_all_books

def main():
    books = get_all_books()
    # NOTE consider making this a map()
    for book in tqdm(books):
        book_url = book['url']
        if book_url is not None:
            GBConvert(book_url).run()


if __name__ == "__main__":
    main()
