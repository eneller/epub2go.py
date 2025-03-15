import requests
from bs4 import BeautifulSoup
from bs4 import ResultSet
from urllib.parse import urljoin
from urllib.request import  urlparse
from tqdm import tqdm
from pyfzf.pyfzf import FzfPrompt
import click

import os, subprocess, shlex, logging
import importlib.resources as pkg_resources
from dataclasses import dataclass
from typing import List

logger = logging.getLogger(__name__)

allbooks_url ='https://www.projekt-gutenberg.org/info/texte/allworka.html'

@dataclass
class Book():
    author: str
    title: str
    url: str
class GBConvert():
    def __init__(self,
        url:str,
        author:str = None,
        title:str = None,
        downloaddir = './',
        showprogress:bool = False,
        ):
        # NOTE move non-code files to data folder
        self.style_path_drama = pkg_resources.files('epub2go').joinpath("drama.css")
        with open(pkg_resources.files('epub2go').joinpath('blocklist.txt')) as blocklist:
            self.blocklist = blocklist.read().splitlines()
        self.tocpage = os.path.dirname(url) # ToC website url
        url = urlparse(self.tocpage)
        self.dir_download = downloaddir
        self.dir_output = os.path.join(self.dir_download, url.netloc + url.path )# directories created by wget recreating the URL
        logger.debug('Downloading in %s, expecting files in in %s', self.dir_download, self.dir_output)
        self.showprogress = showprogress
        self.author = author
        self.title = title
        self.chapters = []

        self.parse_meta()
        
    def parse_meta(self):
        response = requests.get(self.tocpage)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        # TODO allow setting these from interactive mode where those parameters are figured out from the list
        if not self.author:
            try:
                self.author = soup.find('meta', {'name': 'author'})['content']
            except:
                self.author = "UnknownAuthor"
        if not self.title:
            try:
                self.title = soup.find('meta', {'name': 'title'})['content']
            except:
                self.title = "UnknownTitle"
        self.toc = soup.find('ul').find_all('a')
        logger.debug('Found ToC with %d entries', len(self.toc))
        
    def parse_toc_entry(self, entry):
        url = os.path.join(self.tocpage, entry['href'])
        self.save_page(url)
        return url

    # apply blocklist to file
    def parse_page(self,file_path):
        #TODO clean up file opening, mmap?
        logger.debug('Parsing page at %s', file_path)
        with open(file_path, 'r+') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            for blocker in self.blocklist:
                for item in soup.select(blocker):
                    item.decompose()
            f.write(str(soup))

    def create_epub(self,  filename='out.epub')-> int:
        #TODO --epub-cover-image
        #TODO toc if it isnt described by <h> tags, e.g. https://www.projekt-gutenberg.org/adlersfe/maskenba/
        logger.debug('Creating epub as "%s"',filename)
        command = f'''pandoc -f html -t epub \
                    -o "{filename}" \
                    --reference-location=section \
                    --css="{self.style_path_drama}" \
                    --metadata title="{self.title}" \
                    --metadata author="{self.author}" \
                    --epub-title-page=false \
                    {" ".join(self.chapters)} '''
        return subprocess.run(shlex.split(command), cwd=self.dir_output).returncode

    def save_page(self, url):
        logger.debug('Saving page at %s', url)
        # https://superuser.com/questions/970323/using-wget-to-copy-website-with-proper-layout-for-offline-browsing
        command = f'''wget \
                    --timestamping \
                    --page-requisites \
                    --convert-links \
                    --tries=5 \
                    --quiet \
                    {url}'''
        return subprocess.run(shlex.split(command), cwd=self.dir_download).returncode
    def run(self):
        #TODO include images flag

        # download all files in toc (chapters)
        for item in (tqdm(self.toc) if self.showprogress else self.toc):
            item_url = self.parse_toc_entry(item)
            parsed_url = urlparse(item_url)
            filepath = os.path.join(self.dir_download, parsed_url.netloc + parsed_url.path)
            self.parse_page(filepath)
            self.chapters.append(os.path.basename(item_url))
        
        return self.create_epub(f'{self.title} - {self.author}.epub')

# get a list of all books for interactive selection or scraping
def get_all_books() -> List[Book]:
    response = requests.get(allbooks_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser', from_encoding='utf-8')
    tags = soup.find('dl').findChildren()
    books = []
    for tag in tags:
        # is description tag, i.e. contains author name
        if tag.name =='dt':
            # update author
            # special case when author name and Alphabetical list is in same tag
            br_tag = tag.find('br')
            if br_tag:
                book_author = str(br_tag.next_sibling)
            # default case, dt only contains author name
            else:
                book_author = tag.get_text(strip=True)
            book_author = ' '.join(book_author.split())
        # is details tag, contains book url
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
    logging.basicConfig(level=logging.ERROR,format='%(asctime)s - %(levelname)s - %(message)s')
    if(debug): logger.setLevel(logging.DEBUG)
    # non-interactive mode
    if len(args) > 0 :
        books = args
    # interactive mode using fzf
    else:
        logger.debug('Received no CLI arguments, starting interactive mode')
        delimiter = ';'
        # create lines for fzf
        books = [f"{ item.author } - { item.title } {delimiter} { item.url }" for item in get_all_books()]
        fzf = FzfPrompt()
        selection = fzf.prompt(choices=books,  fzf_options=r'--exact --with-nth 1 -m -d\;')
        books = [item.split(';')[1].strip() for item in selection]

    logger.debug('Attempting to download from %d URL(s)', len(books))
    if len(books)==1:
        GBConvert(books[0], showprogress=not silent).run()
    else:
        for book in (tqdm(books) if not silent else books):
                GBConvert(book).run()
if __name__ == "__main__":
    main()
