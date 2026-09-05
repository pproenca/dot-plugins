import unittest

from events import page


class EventSmokeTests(unittest.TestCase):
    def test_empty_feed(self):
        self.assertEqual(page([], "acme"), {"items": [], "next_cursor": None})

    def test_simple_pages(self):
        events = [
            {"id": str(i), "tenant": "acme", "status": "open", "created_at": i}
            for i in range(3)
        ]
        first = page(events, "acme", limit=2)
        self.assertEqual(first["items"], events[:2])
        self.assertIsInstance(first["next_cursor"], str)
        second = page(events, "acme", limit=2, cursor=first["next_cursor"])
        self.assertEqual(second, {"items": events[2:], "next_cursor": None})


if __name__ == "__main__":
    unittest.main()
