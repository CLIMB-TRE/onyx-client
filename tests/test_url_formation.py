import unittest
import posixpath


class TestURLFormation(unittest.TestCase):

    def test_with_trailing_slash(self):
        resultant_url: str = posixpath.join("https://onyx-test.climb.ac.uk/", "B", "c")
        self.assertEqual(resultant_url, "https://onyx-test.climb.ac.uk/B/c")

    def test_without_trailing_slash(self):
        resultant_url: str = posixpath.join("https://onyx-test.climb.ac.uk", "B", "c")
        self.assertEqual(resultant_url, "https://onyx-test.climb.ac.uk/B/c")

    def test_with_trailing_slash_in_middle(self):
        resultant_url: str = posixpath.join("https://onyx-test.climb.ac.uk", "B/", "c")
        self.assertEqual(resultant_url, "https://onyx-test.climb.ac.uk/B/c")

    def test_with_trailing_slash_at_end(self):
        resultant_url: str = posixpath.join("https://onyx-test.climb.ac.uk", "B", "c/")
        #This test should retain the slash
        self.assertEqual(resultant_url, "https://onyx-test.climb.ac.uk/B/c/")

if __name__ == '__main__':
    unittest.main()
