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
        
    def get_meta(self):
        response = requests.get(self.root)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        self.author = soup.find('meta', {'name': 'author'})['content']
        self.title = soup.find('meta', {'name': 'title'})['content']
        self.toc = soup.find('ul').find_all('a')
    
    def save_page(self, url):
        # TODO fix redownloading of shared content
        # https://superuser.com/questions/970323/using-wget-to-copy-website-with-proper-layout-for-offline-browsing
        command = f'''wget \
                    --page-requisites \
                    --convert-links \
                    --execute \
                    --tries=5 \
                    --quiet \
                    {url}'''
        os.system(command)

    def clean_page(self,file_path):
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

    def run(self):
        #TODO include images flag

        self.get_meta()

        map(lambda x: self.save_page(os.path.join(self.root, x['href'])), self.toc)
        self.chapters = []
        for item in (tqdm(self.toc) if self.standalone else self.toc):
            item_title= item.get_text()
            item_url = os.path.join(self.root, item['href'])
            self.save_page(url=item_url)
            parsed_url = urlparse(item_url)
            filepath = parsed_url.netloc + parsed_url.path
            self.clean_page(filepath)
            self.chapters.append(item['href'])
        
        self.create_epub(f'{self.title} - {self.author}.epub')
        
def get_all_books() -> list:
    books = get_all_book_tags()
    d = []
    for book in books:
        book_href = book.get('href')
        if book_href is not None:
            book_url = urljoin(allbooks_url, book_href)
            book_title = book.getText().translate(str.maketrans('','', '\n\t'))
            d.append({'title': book_title, 'url': book_url})
    return d

def get_all_book_tags ()-> ResultSet:
    response = requests.get(allbooks_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser', from_encoding='utf-8')
    books = soup.find('dl').find_all('a')
    return books
    
def main():
    sys.argv.pop(0)
    # non-interactive mode
    if len(sys.argv) > 0 :
        books = sys.argv
    # interactive mode using fzf
    else:
        delimiter = ';'
        # create lines for fzf
        # TODO display author
        books = [f"{item['title']} {delimiter} {item['url']}" for item in get_all_books()]
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
