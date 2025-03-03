import requests
from bs4 import BeautifulSoup
from bs4 import ResultSet
from urllib.parse import urljoin
from urllib.request import  urlparse
from tqdm import tqdm
from pyfzf.pyfzf import FzfPrompt

import os, sys
import importlib.resources as pkg_resources


allbooks_url ='https://www.projekt-gutenberg.org/info/texte/allworka.html'
root_url = '{url.scheme}://{url.netloc}'.format(url = urlparse(allbooks_url))

class GBConvert():
    #TODO fix toc / headings
    
    def __init__(self,
        url:str,
        standalone = False,
        ):
        # NOTE move non-code files to data folder
        self.style_path_drama = pkg_resources.files('epub2go').joinpath("drama.css")
        self.blocklist = open(pkg_resources.files('epub2go').joinpath('blocklist.txt')).read().splitlines()
        self.root = os.path.dirname(url)
        self.url = urlparse(self.root)
        self.output = self.url.netloc + self.url.path
        self.standalone = standalone
        self.chapters = []
        
    def parse_meta(self):
        response = requests.get(self.root)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        self.author = soup.find('meta', {'name': 'author'})['content']
        self.title = soup.find('meta', {'name': 'title'})['content']
        self.toc = soup.find('ul').find_all('a')
        
    def parse_toc_entry(self, entry):
        url = os.path.join(self.root, entry['href'])
        self.save_page(url)
        return url

    def parse_page(self,file_path):
        f = open(file_path, 'r').read()
        soup = BeautifulSoup(f, 'html.parser')
        for blocker in self.blocklist:
            for item in soup.select(blocker):
                item.decompose()
        open(file_path, 'w').write(str(soup))


    def create_epub(self,  filename='out.epub'):
        os.chdir(self.output)
        command = f'''pandoc -f html -t epub \
                    -o "{filename}" \
                    --reference-location=section \
                    --css="{self.style_path_drama}" \
                    --metadata title="{self.title}" \
                    --metadata author="{self.author}" \
                    --epub-title-page=false \
                    {" ".join(self.chapters)} '''#TODO --epub-cover-image
        os.system(command)

    def save_page(self, url):
        # https://superuser.com/questions/970323/using-wget-to-copy-website-with-proper-layout-for-offline-browsing
        command = f'''wget \
                    --timestamping \
                    --page-requisites \
                    --convert-links \
                    --tries=5 \
                    --quiet \
                    {url}'''
        os.system(command)
    def run(self):
        #TODO include images flag

        self.parse_meta()
        # download all files in toc (chapters)
        for item in (tqdm(self.toc) if self.standalone else self.toc):
            item_url = self.parse_toc_entry(item)
            parsed_url = urlparse(item_url)
            filepath = parsed_url.netloc + parsed_url.path
            self.parse_page(filepath)
            self.chapters.append(os.path.basename(item_url))
        
        self.create_epub(f'{self.title} - {self.author}.epub')

# Methods used to get a list of all books for interactive selection or scraping
def get_all_books() -> list:
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
                book = {'author': book_author, 'title': book_title, 'url': book_url}
                books.append(book)
    return books

def get_all_book_tags ()-> ResultSet:
    response = requests.get(allbooks_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser', from_encoding='utf-8')
    books = soup.find('dl').find_all('a')
    return books
    
# run main cli
def main():
    sys.argv.pop(0)
    # non-interactive mode
    if len(sys.argv) > 0 :
        books = sys.argv
    # interactive mode using fzf
    else:
        delimiter = ';'
        # create lines for fzf
        books = [f"{item['author']} - {item['title']} {delimiter} {item['url']}" for item in get_all_books()]
        fzf = FzfPrompt()
        selection = fzf.prompt(choices=books,  fzf_options=r'--exact --with-nth 1 -m -d\;')
        books = [item.split(';')[1].strip() for item in selection]

    if len(books)==1:
        GBConvert(books[0], standalone=True).run()
    else:
        for book in tqdm(books):
                GBConvert(book).run()
if __name__ == "__main__":
    main()
