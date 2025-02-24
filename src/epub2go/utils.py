from bs4 import BeautifulSoup
import requests

from urllib.parse import urlparse

allbooks_url ='https://www.projekt-gutenberg.org/info/texte/allworka.html'
root_url = '{url.scheme}://{url.netloc}'.format(url = urlparse(allbooks_url))

def get_all_book_urls():
    response = requests.get(allbooks_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')
    books = soup.find('dl').find_all('a')
    return books