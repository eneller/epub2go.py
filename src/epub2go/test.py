import requests
from bs4 import BeautifulSoup

import os

from convert import GBConvert

def main():
    allbooks_relative_url ='/info/texte/allworka.html'
    root_url = 'https://www.projekt-gutenberg.org'
    allbooks_url = root_url + allbooks_relative_url
    response = requests.get(allbooks_url)
    if (response.status_code != 200): raise Exception(f'Couldnt fetch root page {self.root}')
    soup = BeautifulSoup(response.content, 'html.parser')
    books = soup.find('dl').find_all('a')
    for book in books:
        book_title = book.get_text()
        book_url_relative = book.get('href')
        if book_url_relative is not None:
            book_url = root_url + os.path.dirname(book_url_relative)[5:]
            gb = GBConvert(book_url)


if __name__ == "__main__":
    main()