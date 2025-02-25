import requests
from tqdm import tqdm

import os
from urllib.parse import urljoin

from convert import GBConvert, get_all_book_tags, allbooks_url

def main():
    books = get_all_book_tags()
    # NOTE consider making this a map()
    for book in tqdm(books):
        book_title = book.get_text()
        book_url_relative = book.get('href')
        if book_url_relative is not None:
            book_url = urljoin(allbooks_url, book_url_relative)
            GBConvert(book_url).run()


if __name__ == "__main__":
    main()
