import unittest

from raspberrytv.telegram_client import extract_url, select_latest_url


class TelegramParsingTests(unittest.TestCase):
    def test_explicit_and_plain_url(self):
        self.assertEqual(extract_url("URL https://example.com/a"), "https://example.com/a")
        self.assertEqual(extract_url("Guarda https://example.org/x."), "https://example.org/x")
        self.assertIsNone(extract_url("ftp://example.com"))

    def test_selects_latest_valid_message_for_chat_and_topic(self):
        updates = [
            {"update_id": 10, "message": {"message_id": 1, "date": 100, "chat": {"id": -1}, "message_thread_id": 9, "text": "https://old.example"}},
            {"update_id": 11, "message": {"message_id": 2, "date": 300, "chat": {"id": -2}, "message_thread_id": 9, "text": "https://wrong-chat.example"}},
            {"update_id": 12, "message": {"message_id": 3, "date": 200, "chat": {"id": -1}, "message_thread_id": 8, "text": "https://wrong-topic.example"}},
            {"update_id": 13, "message": {"message_id": 4, "date": 400, "chat": {"id": -1}, "message_thread_id": 9, "text": "URL https://new.example/path"}},
        ]
        selected = select_latest_url(updates, "-1", "9")
        self.assertEqual(selected.url, "https://new.example/path")
        self.assertEqual(selected.message_id, 4)
        self.assertEqual(selected.newest_update_id, 13)

    def test_advances_offset_even_without_valid_url(self):
        selected = select_latest_url([{"update_id": 99, "message": {"chat": {"id": 1}, "text": "no"}}], "1")
        self.assertIsNone(selected.url)
        self.assertEqual(selected.newest_update_id, 99)


if __name__ == "__main__":
    unittest.main()
