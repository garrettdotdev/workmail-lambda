import unittest
from workmail_common.utils import extract_domain


class TestExtractDomain(unittest.TestCase):

    def test_extract_domain_valid_url(self):
        url = "http://blog.example.com"
        full_domain, root_domain = extract_domain(url)
        self.assertEqual(full_domain, "blog.example.com")
        self.assertEqual(root_domain, "example")

    def test_extract_domain_valid_url_with_https(self):
        url = "https://blog.example.com"
        full_domain, root_domain = extract_domain(url)
        self.assertEqual(full_domain, "blog.example.com")
        self.assertEqual(root_domain, "example")

    def test_extract_domain_valid_url_without_scheme(self):
        url = "blog.example.com"
        full_domain, root_domain = extract_domain(url)
        self.assertEqual(full_domain, "blog.example.com")
        self.assertEqual(root_domain, "example")

    def test_extract_domain_valid_url_with_www(self):
        url = "http://www.example.com"
        full_domain, root_domain = extract_domain(url)
        self.assertEqual(full_domain, "example.com")
        self.assertEqual(root_domain, "example")

    def test_extract_domain_invalid_url(self):
        url = "http://invalid-url"
        with self.assertRaises(Exception) as context:
            extract_domain(url)
        self.assertEqual(str(context.exception), "Invalid domain name: 'invalid-url'")

    def test_extract_domain_invalid_domain(self):
        url = "invalid-url"
        with self.assertRaises(Exception) as context:
            extract_domain(url)
        self.assertEqual(str(context.exception), "Invalid domain name: 'invalid-url'")

    def test_extract_domain_no_hostname(self):
        url = "http://"
        with self.assertRaises(Exception) as context:
            extract_domain(url)
        self.assertEqual(
            str(context.exception), "Invalid URL or domain name: 'http://'"
        )

    def test_extract_domain_single_part_domain(self):
        url = "http://localhost"
        with self.assertRaises(Exception) as context:
            extract_domain(url)
        self.assertEqual(str(context.exception), "Invalid domain name: 'localhost'")


if __name__ == "__main__":
    unittest.main()
