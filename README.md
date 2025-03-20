# epub2go.py
Web to ePUB Converter for [projekt-gutenberg.org](https://projekt-gutenberg.org)  developed in conjunction with a [web interface](https://github.com/eneller/epub2go-web).

## Installation
Requires:
- [pandoc](https://pandoc.org/)
- [wget](https://www.gnu.org/software/wget/)
- [fzf](https://github.com/junegunn/fzf) (optional, only for interactive mode)
- [python](https://www.python.org/) (duh)

Assuming you have a recent version of python installed, run

```
pip install git+https://github.com/eneller/epub2go.py
```
This will provide the `epub2go` command.

## Usage
```
Usage: epub2go [OPTIONS] [ARGS]...

  Download ePUBs from https://www.projekt-gutenberg.org/

  Provide either 0 arguments to enter interactive mode or an arbitrary number
  of URLs to download from

Options:
  -d, --debug      Set the log level to DEBUG
  -s, --silent     Disable the progress bar
  -p, --path TEXT  The path to which files are saved
  --no-clean       Do not parse html files with blocklist
  --help           Show this message and exit.
```

Examples:
```bash
epub2go https://www.projekt-gutenberg.org/ibsen/solness/
epub2go # will enter interactive mode
```
