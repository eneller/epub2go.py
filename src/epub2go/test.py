import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from urllib.request import urlparse
from tqdm import tqdm
from pyfzf.pyfzf import FzfPrompt
import click

import os, subprocess, shlex, logging
import importlib.resources as pkg_resources
from dataclasses import dataclass
from typing import List

logger = logging.getLogger(__name__)

allbooks_url = 'https://www.projekt-gutenberg.org/info/texte/allworka.html'

@dataclass
class Book():
    author: str
    title: str
    url: str

class GBConvert():
    def __init__(self, downloaddir):
        # NOTE move non-code files to data folder
        self.style_path_drama = pkg_resources.files('epub2go').joinpath("drama.css")
        with open(pkg_resources.files('epub2go').joinpath('blocklist.txt')) as blocklist:
            self.blocklist = blocklist.read().splitlines()
        self.dir_download = downloaddir

    def download(self, url: str, author: str = None, title: str = None, showprogress: bool = False):
        tocpage = os.path.dirname(url)  # ToC website url
        url = urlparse(tocpage)
        dir_output = os.path.join(self.dir_download, url.netloc + url.path)  # directories created by wget recreating the URL
        logger.debug('Downloading in %s, expecting files in %s', self.dir_download, dir_output)

        response = requests.get(tocpage)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        if not author:
            try:
                author = soup.find('meta', {'name': 'author'})['content']
            except:
                author = "UnknownAuthor"
        if not title:
            try:
                title = soup.find('meta', {'name': 'title'})['content']
            except:
                title = "UnknownTitle"
        
        toc = soup.find('ul').find_all('a')
        logger.debug('Found ToC with %d entries', len(toc))
        
        chapters = []
        for item in (tqdm(toc) if showprogress else toc):
            item_url = self.parse_toc_entry(tocpage, item)
            parsed_url = urlparse(item_url)
            filepath = os.path.join(self.dir_download, parsed_url.netloc + parsed_url.path)
            self.parse_page(filepath)
            chapters.append(os.path.basename(item_url))
        
        return self.create_epub(author, title, chapters, dir_output)

    def parse_toc_entry(self, tocpage, entry):
        url = os.path.join(tocpage, entry['href'])
        self.save_page(url)
        return url

    def parse_page(self, file_path):
        logger.debug('Parsing page at %s', file_path)
        with open(file_path, 'r+') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            for blocker in self.blocklist:
                for item in soup.select(blocker):
                    item.decompose()
            f.seek(0)
            f.truncate()
            f.write(str(soup))

    def create_epub(self, author, title, chapters, dir_output) -> int:
        filename = f'{title} - {author}.epub'
        logger.debug('Creating epub as "%s"', filename)
        command = f'''pandoc -f html -t epub \
                    -o "{filename}" \
                    --reference-location=section \
                    --css="{self.style_path_drama}" \
                    --metadata title="{title}" \
                    --metadata author="{author}" \
                    --epub-title-page=false \
                    {" ".join(chapters)} '''
        return subprocess.run(shlex.split(command), cwd=dir_output).returncode

    def save_page(self, url):
        logger.debug('Saving page at %s', url)
        command = f'''wget \
                    --timestamping \
                    --page-requisites \
                    --convert-links \
                    --tries=5 \
                    --quiet \
                    {url}'''
        return subprocess.run(shlex.split(command), cwd=self.dir_download).returncode

# get a list of all books for interactive selection or scraping
def get_all_books() -> List[Book]:
    response = requests.get(allbooks_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser', from_encoding='utf-8')
    tags = soup.find('dl').findChildren()
    books = []
    for tag in tags:
        if tag.name == 'dt':
            br_tag = tag.find('br')
            if br_tag:
                book_author = str(br_tag.next_sibling)
            else:
                book_author = tag.get_text(strip=True)
            book_author = ' '.join(book_author.split())
        elif tag.name == 'dd':
            book_tag = tag.a
            if book_tag:
                book_href = book_tag.get('href')
                book_url = urljoin(allbooks_url, book_href)
                book_title = ' '.join(book_tag.getText().split())
                book = Book(book_author, book_title, book_url)
                books.append(book)
    return books

# run main cli
@click.command()
@click.option('--debug', '-d', is_flag=True, help='Set the log level to DEBUG')
@click.option('--silent', '-s', is_flag=True, help='Disable the progress bar')
@click.argument('args', nargs=-1)
def main(args, debug, silent):
    '''
    Download ePUBs from https://www.projekt-gutenberg.org/
    Provide either 0 arguments to enter interactive mode or an arbitrary number of URLs to download from
    '''
    logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
    if(debug): logger.setLevel(logging.DEBUG)
    # non-interactive mode
    if len(args) > 0:
        books = args
    else:
        logger.debug('Received no CLI arguments, starting interactive mode')
        delimiter = ';'
        books = [f"{ item.author } - { item.title } {delimiter} { item.url }" for item in get_all_books()]
        fzf = FzfPrompt()
        selection = fzf.prompt(choices=books, fzf_options=r'--exact --with-nth 1 -m -d\;')
        books = [item.split(';')[1].strip() for item in selection]

    logger.debug('Attempting to download from %d URL(s)', len(books))
    converter = GBConvert('./')
    if len(books) == 1:
        converter.download(books[0], showprogress=not silent)
    else:
        for book in (tqdm(books) if not silent else books):
            converter.download(book)

if __name__ == "__main__":
    main()