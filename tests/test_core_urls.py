from __future__ import annotations

import unittest

from multidownloader.core.urls import parse_urls, unique_urls


class TestCoreUrls(unittest.TestCase):
    def test_parse_urls_ignores_comments_blanks_and_deduplicates(self) -> None:
        text = """
        # comment
        https://example.com/1

          https://example.com/2
        https://example.com/1
        """
        self.assertEqual(
            parse_urls(text),
            ["https://example.com/1", "https://example.com/2"],
        )

    def test_unique_urls_strips_and_deduplicates(self) -> None:
        self.assertEqual(
            unique_urls(["  https://a  ", "", "https://a", "https://b"]),
            ["https://a", "https://b"],
        )


if __name__ == "__main__":
    unittest.main()
