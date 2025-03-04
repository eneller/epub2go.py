from tqdm import tqdm

from src.epub2go.convert import GBConvert, get_all_books

import unittest

# run using `python -m unittest test/test_epub.py`
class TestEpub(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.schiller_raeuber = GBConvert('https://www.projekt-gutenberg.org/schiller/raeuber/')
        cls.anzengru_allersee = GBConvert('https://www.projekt-gutenberg.org/anzengru/allersee/')

    def test_schiller_raeuber_toc(self):
        self.assertEqual(len(self.schiller_raeuber.toc), 7)

    def test_anzengru_allersee_toc(self):
        self.assertEqual(len(self.anzengru_allersee.toc), 1)
        

if __name__ == '__main__':
    unittest.main()
