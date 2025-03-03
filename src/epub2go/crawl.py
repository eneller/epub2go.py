import requests
from tqdm import tqdm
from bs4 import BeautifulSoup
from bs4 import ResultSet

import os
from urllib.parse import urljoin

from convert import GBConvert, allbooks_url

def parse_book_tags ()-> ResultSet:
    response = requests.get(allbooks_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser', from_encoding='utf-8')
    books = soup.find('dl').find_all('a')
    books = [(book.get_text(), book.get('href')) for book in books]
    return books

def main():
    books = parse_book_tags()
    # NOTE consider making this a map()
    for book in tqdm(parse_book_tags()):
        (book_title, book_url_relative) = book
        if book_url_relative is not None:
            book_url = urljoin(allbooks_url, book_url_relative)
            GBConvert(book_url).run()


if __name__ == "__main__":
    main()
