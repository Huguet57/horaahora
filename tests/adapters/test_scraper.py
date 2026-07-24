import unittest

from scraper import Entry


class EntryDestinationTests(unittest.TestCase):
    def test_associated_link_is_the_entry_destination(self):
        entry = Entry(
            title="Notícia breu",
            excerpt="Més informació. Entreu aquí.",
            url="https://revistacastells.cat/hora-a-hora/noticia-breu/",
            date="21 juliol, 2026",
            embedded_url="https://revistacastells.cat/2026/07/article-complet/",
        )

        self.assertEqual(
            entry.destination_url,
            "https://revistacastells.cat/2026/07/article-complet/",
        )

    def test_entry_has_no_destination_when_excerpt_has_no_link(self):
        entry = Entry(
            title="Notícia sense enllaç associat",
            excerpt="Només un resum.",
            url="https://revistacastells.cat/hora-a-hora/noticia-breu/",
            date="21 juliol, 2026",
        )

        self.assertEqual(entry.destination_url, "")

if __name__ == "__main__":
    unittest.main()
