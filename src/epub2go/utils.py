from bs4 import BeautifulSoup, ResultSet
import requests

from urllib.parse import urlparse, urljoin
import os
import json
import unicodedata

allbooks_url ='https://www.projekt-gutenberg.org/info/texte/allworka.html'
root_url = '{url.scheme}://{url.netloc}'.format(url = urlparse(allbooks_url))


def get_all_book_urls ()-> ResultSet:
    response = requests.get(allbooks_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser', from_encoding='utf-8')
    books = soup.find('dl').find_all('a')
    return books

def main():
    books = get_all_book_urls()
    d = []
    for book in books:
        book_href = book.get('href')
        if book_href is not None:
            book_url = urljoin(allbooks_url, book_href)
            book_title = book.getText().translate(str.maketrans('','', '\n\t'))
            d.append({'title': book_title, 'url': book_url})

    json.dump(d, open('dict.json', 'w' ), ensure_ascii=False)
    print(len(d))
    
if __name__ == '__main__':
    main()