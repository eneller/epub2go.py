import requests
from bs4 import BeautifulSoup
from bs4 import ResultSet
from urllib.parse import urljoin
from urllib.request import  urlparse
from tqdm import tqdm
from pyfzf.pyfzf import FzfPrompt
import click

import os, subprocess, shlex, logging, re
import concurrent.futures
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
        downloaddir,
        ):
        # NOTE move non-code files to data folder
        self.style_path_drama = pkg_resources.files('epub2go').joinpath("drama.css")
        with open(pkg_resources.files('epub2go').joinpath('blocklist.txt')) as blocklist:
            self.blocklist = blocklist.read().splitlines()
        self.dir_download = downloaddir

    def getDir(self, url):
        tocpage = os.path.dirname(url) # ToC website url
        parsed_url = urlparse(tocpage)
        # directories created by wget recreating the URL
        dir_output = os.path.join(self.dir_download, parsed_url.netloc + parsed_url.path )
        return dir_output
        
    def download(self,
        url:str,
        author:str = None,
        title:str = None,
        showprogress: bool = False,
        cleanpages: bool = True,
        max_workers: int = 10,
    ):
        tocpage = os.path.dirname(url) # ToC website url
        dir_output = self.getDir(url)
        logger.debug('Downloading to %s, expecting files in in %s', self.dir_download, dir_output)
        author = author
        title = title

        #parse_meta
        response = requests.get(tocpage)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        # TODO allow setting these from interactive mode where those parameters are figured out from the list
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
        chapter_urls = soup.find('ul').find_all('a')
        logger.debug('Found ToC with %d entries', len(chapter_urls))

        #run
        #TODO include images flag
        # download all files in toc (chapters)
        def process_item(item):
            item_url = self.parse_toc_entry(tocpage, item)
            parsed_url = urlparse(item_url)
            filepath = os.path.join(self.dir_download, parsed_url.netloc + parsed_url.path)
            if cleanpages:
                self.parse_page(filepath)
            return os.path.basename(item_url)

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            items = tqdm(chapter_urls) if showprogress else chapter_urls
            for item in items:
                futures.append(executor.submit(process_item, item))

            # Wait for completion and preserve order
            chapter_files = [future.result() for future in futures]
        
        return self.create_epub(author,title,chapter_files,dir_output)
        
    def parse_toc_entry(self, tocpage, entry):
        url = os.path.join(tocpage, entry['href'])
        self.save_page(url)
        return url

    # apply blocklist to file
    def parse_page(self,file_path):
        #TODO clean up file opening, mmap?
        count=0
        with open(file_path, 'r+') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            for blocker in self.blocklist:
                for item in soup.select(blocker):
                    item.decompose()
                    count+=1
            f.seek(0)
            f.truncate()
            f.write(str(soup))
        logger.debug('Removed %d tags from page %s during parsing', count, file_path)

    def create_epub(self, author, title, chapters, dir_output):
        #TODO --epub-cover-image
        #TODO toc if it isnt described by <h> tags, e.g. https://www.projekt-gutenberg.org/adlersfe/maskenba/
        filename = slugify(f'{title} - {author}.epub')
        command = f'''pandoc -f html -t epub \
                    -o "{filename}" \
                    --reference-location=section \
                    --css="{self.style_path_drama}" \
                    --metadata title="{title}" \
                    --metadata author="{author}" \
                    --epub-title-page=false \
                    {" ".join(chapters)} '''
        logger.debug('Calling "%s"', command)
        subprocess.run(shlex.split(command), cwd=dir_output, check=True)
        return os.path.abspath(os.path.join(dir_output,filename))

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
        subprocess.run(shlex.split(command), cwd=self.dir_download, check=True)

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

def slugify(value, replacement='_'):
    value = re.sub(r'[<>:"/\\|?*\x00-\x1F]', replacement, value)
    # Remove leading/trailing whitespace or dots
    value = value.strip().strip(".")
    # Optionally truncate to safe length (e.g. 255 chars for most filesystems)
    return value[:255] or "untitled"

# run main cli
@click.command()
#TODO include images flag
@click.option('--debug', '-d', is_flag=True, help='Set the log level to DEBUG')
@click.option('--silent', '-s', is_flag=True, help='Disable the progress bar')
@click.option('--path','-p',type=str,default='./', help='The path to which files are saved' )
@click.option('--no-clean',is_flag=True,help='Do not parse html files with blocklist')
@click.option('--max-workers', '-w', type=int, default=10, help='Number of concurrent download workers')
@click.argument('args', nargs=-1)
def main(args, debug, silent, path, no_clean, max_workers):
    '''
    Download ePUBs from https://www.projekt-gutenberg.org/ \n
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
    converter = GBConvert(path)
    if len(books)==1:
        converter.download(books[0], showprogress=not silent, cleanpages= not no_clean, max_workers=max_workers)
    else:
        for book in (tqdm(books) if not silent else books):
            converter.download(book, cleanpages= not no_clean, max_workers=max_workers)

if __name__ == "__main__":
    main()
