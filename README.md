# epub2go.py
web to epub converter for https://projekt-gutenberg.org.
Requires:
- [pandoc](https://pandoc.org/)
- [wget](https://www.gnu.org/software/wget/)
- [fzf](https://github.com/junegunn/fzf) (only for interactive mode)
- python (duh)
## Usage
Invoke the script using the url of any page of the book you would like to download:
``` 
epub2go https://www.projekt-gutenberg.org/ibsen/solness/
```
## Installation
   Assuming you have a recent version of python installed, run
   ```
   pip install git+https://github.com/eneller/epub2go.py
   ```
   This will provide the 'epub2go' command.
