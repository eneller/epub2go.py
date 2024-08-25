# epub2go.py
web to epub converter for https://projekt-gutenberg.org.
Requires:
- [pandoc](https://pandoc.org/)
- wget
- python
## Usage
Invoke the script using the url of any page of the book you would like to download:
``` 
python convert.py https://example.com
```
## Installation
1. Assuming you have a recent version of [Python](https://www.python.org/downloads/) and Pip installed, create virtual environment using
   ```
   python -m venv .venv
   ```
2. Activate your new venv using
   ```
   source .venv/bin/activate
   ```
3. Install the requirements for this script using
   ```
   pip install -r requirements.txt
   ```
