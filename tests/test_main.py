import importlib
import sys
import types
import unittest
from unittest.mock import Mock, patch

from scraper import Entry


notifier_stub = types.ModuleType("notifier")
notifier_stub.create_notifier = Mock()
with patch.dict(sys.modules, {"notifier": notifier_stub}):
    main = importlib.import_module("main")


class NotificationDestinationTests(unittest.TestCase):
    @patch("builtins.print")
    @patch.object(main, "save_state")
    @patch.object(main, "create_notifier")
    @patch.object(main, "load_state")
    @patch.object(main, "fetch_entries")
    def test_notification_opens_associated_link(
        self,
        fetch_entries,
        load_state,
        create_notifier,
        _save_state,
        _print,
    ):
        fetch_entries.return_value = [Entry(
            title="Dimarts 21, 10h. Notícia breu",
            excerpt="Més informació. Entreu aquí.",
            url="https://revistacastells.cat/hora-a-hora/noticia-breu/",
            date="21 juliol, 2026",
            embedded_url="https://revistacastells.cat/2026/07/article-complet/",
        )]
        load_state.return_value = {"last_hash": "un-hash-anterior"}
        notifier = Mock()
        create_notifier.return_value = notifier

        main.main()

        notifier.send.assert_called_once_with(
            title="Notícia breu",
            body="Dimarts 21, 10h. Més informació. Entreu aquí.",
            url="https://revistacastells.cat/2026/07/article-complet/",
        )


if __name__ == "__main__":
    unittest.main()
