"""Behavioral checks for the event feed contract."""

import copy
import itertools
import unittest

from events import page


def event(ident, timestamp, tenant="acme", status="open"):
    return {"id": ident, "created_at": timestamp, "tenant": tenant, "status": status,
            "payload": {"label": ident, "values": [timestamp]}}


class PaginationContractTests(unittest.TestCase):
    def walk(self, rows, tenant="acme", status=None, reverse=False, limits=(2,)):
        original = copy.deepcopy(rows)
        expected = sorted(
            [row for row in rows
             if row["tenant"] == tenant and (status is None or row["status"] == status)],
            key=lambda row: (row["created_at"], row["id"]), reverse=reverse,
        )
        cursor = None
        seen_cursors = set()
        consumed = 0
        collected = []
        for limit in itertools.islice(itertools.cycle(limits), len(expected) + 2):
            result = page(rows, tenant, status=status, limit=limit,
                          cursor=cursor, reverse=reverse)
            self.assertEqual(set(result), {"items", "next_cursor"})
            self.assertIsInstance(result["items"], list)
            self.assertEqual(result["items"], expected[consumed:consumed + limit])
            self.assertEqual(rows, original, "Input events changed")
            replay = page(rows, tenant, status=status, limit=limit,
                          cursor=cursor, reverse=reverse)
            self.assertEqual(replay["items"], result["items"])
            self.assertEqual(replay["next_cursor"] is None, result["next_cursor"] is None)
            collected.extend(result["items"])
            consumed += len(result["items"])
            cursor = result["next_cursor"]
            if consumed == len(expected):
                self.assertIsNone(cursor)
                self.assertEqual(collected, expected)
                return
            self.assertIsInstance(cursor, str)
            self.assertTrue(cursor)
            self.assertNotIn(cursor, seen_cursors, "Cursor loop")
            seen_cursors.add(cursor)
        self.fail("Pagination did not terminate")

    def test_filter_before_page_size(self):
        rows = [event("a", 1, "other"), event("b", 2, status="closed"),
                event("c", 3), event("d", 4, "other"), event("e", 5),
                event("f", 6, status="closed"), event("g", 7)]
        for reverse in (False, True):
            with self.subTest(reverse=reverse):
                self.walk(rows, status="open", reverse=reverse, limits=(2,))

    def test_timestamp_ties_use_id_and_survive_boundaries(self):
        rows = [event(ident, timestamp) for ident, timestamp in
                [("z", 2), ("b", 1), ("a", 1), ("a:2", 2),
                 ("a/1", 1), ("x", 2), ("omega", 3)]]
        for reverse, limits in itertools.product((False, True), ((1,), (2,), (3, 1, 2))):
            with self.subTest(reverse=reverse, limits=limits):
                self.walk(rows, reverse=reverse, limits=limits)

    def test_no_matches_is_terminal(self):
        rows = [event(str(i), i, tenant="other") for i in range(8)]
        self.walk(rows, limits=(2,))
        self.walk(rows, tenant="other", status="missing", reverse=True, limits=(1,))
        self.walk([], limits=(1,))

    def test_nonmatching_tail_does_not_advertise_another_page(self):
        for reverse in (False, True):
            with self.subTest(reverse=reverse):
                rows = [event("only", 9 if reverse else 0)]
                rows += [event(str(i), i, tenant="other") for i in range(1, 9)]
                self.walk(rows, reverse=reverse, limits=(1,))

    def test_empty_string_status_is_a_filter(self):
        rows = [event("a", 0, status="open"), event("b", 1, status=""),
                event("c", 2, status="closed"), event("d", 3, status="")]
        self.walk(rows, status="", limits=(1,))
        self.walk(rows, status="", reverse=True, limits=(2,))

    def test_filter_order_limit_matrix(self):
        rows = [event(f"id-{i:02}", (i * 11) % 7 - 3,
                      tenant=("acme", "other", "third")[i % 3],
                      status=("open", "closed", "")[i // 3 % 3])
                for i in range(45)]
        rows = rows[::2] + rows[1::2][::-1]
        for tenant, status, reverse, limits in itertools.product(
            ("acme", "other", "third", "absent"),
            (None, "open", "closed", "", "absent"),
            (False, True), ((1,), (4,), (100,), (2, 5, 1)),
        ):
            with self.subTest(tenant=tenant, status=status, reverse=reverse, limits=limits):
                self.walk(rows, tenant, status, reverse, limits)

    def test_same_cursor_can_use_a_different_limit(self):
        rows = [event(str(i), i) for i in range(9)]
        cursor = page(rows, "acme", limit=2)["next_cursor"]
        small = page(rows, "acme", limit=1, cursor=cursor)
        large = page(rows, "acme", limit=4, cursor=cursor)
        self.assertEqual(small["items"], rows[2:3])
        self.assertEqual(large["items"], rows[2:6])
        following = page(rows, "acme", limit=10, cursor=large["next_cursor"])
        self.assertEqual(following, {"items": rows[6:], "next_cursor": None})


if __name__ == "__main__":
    unittest.main()
