import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from urllib.request import urlopen, urlparse

import os, sys
from pathlib import Path
class GBConvert():
    #TODO fix toc / headings
    def __init__(self
        , url:str
        ):
        self.root = os.path.dirname(url)
        self.url = urlparse(self.root)
        self.output = self.url.netloc + self.url.path
        self.blocklist = open('blocklist.txt', 'r').read().splitlines()
        
    def get_meta(self):
        response = requests.get(self.root)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        self.author = soup.find('meta', {'name': 'author'})['content']
        self.title = soup.find('meta', {'name': 'title'})['content']
        self.toc = soup.find('ul').find_all('a')
    
    def save_page(self, url):
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
                    --css=../../../drama.css \
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
        for item in self.toc:
            item_title= item.get_text()
            item_url = os.path.join(self.root, item['href'])
            self.save_page(url=item_url)
            parsed_url = urlparse(item_url)
            filepath = parsed_url.netloc + parsed_url.path
            self.clean_page(filepath)
            self.chapters.append(item['href'])
        
        self.create_epub(f'{self.title} - {self.author}.epub')
        
    
    
def main():
    g = GBConvert(sys.argv[1])
    g.run()


if __name__ == "__main__":
    main()