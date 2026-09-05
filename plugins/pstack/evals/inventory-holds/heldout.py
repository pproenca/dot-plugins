import unittest

from inventory import Inventory


class ReservationContract(unittest.TestCase):
    def record(self, key, items, expires_at, status="held"):
        return {"key": key, "items": items, "expires_at": expires_at, "status": status}

    def test_initial_stock_and_independent_instances(self):
        source = {"tea": 4, "mug": 0}
        first = Inventory(source)
        second = Inventory(source)
        source["tea"] = 100
        self.assertEqual(first.stock(), {"tea": 4, "mug": 0})
        self.assertEqual(Inventory({}).stock(), {})
        first.reserve("order", {"tea": 1}, 4)
        first.advance(4)
        second.reserve("order", {"tea": 4}, 1)
        self.assertEqual(first.stock(), {"tea": 4, "mug": 0})
        self.assertEqual(second.stock(), {"tea": 0, "mug": 0})
        self.assertEqual(second.get("order")["status"], "held")

    def test_reservation_deducts_every_item(self):
        inventory = Inventory({"tea": 8, "mug": 2, "sugar": 0})
        self.assertEqual(inventory.reserve("o", {"tea": 3, "mug": 2}, 20),
                         self.record("o", {"tea": 3, "mug": 2}, 20))
        self.assertEqual(inventory.stock(), {"tea": 5, "mug": 0, "sugar": 0})
        self.assertEqual(inventory.get("o"), self.record("o", {"tea": 3, "mug": 2}, 20))

    def test_restock_adds_existing_and_new_skus(self):
        inventory = Inventory({"tea": 3})
        inventory.reserve("o", {"tea": 2}, 10)
        additions = {"tea": 4, "mug": 2}
        self.assertIsNone(inventory.restock(additions))
        additions["mug"] = 100
        self.assertEqual(inventory.stock(), {"tea": 5, "mug": 2})
        inventory.release("o")
        self.assertEqual(inventory.stock(), {"tea": 7, "mug": 2})

    def test_capture_is_idempotent_and_survives_deadline(self):
        inventory = Inventory({"tea": 5})
        inventory.reserve("o", {"tea": 2}, 5)
        expected = self.record("o", {"tea": 2}, 5, "captured")
        self.assertEqual(inventory.capture("o"), expected)
        self.assertEqual(inventory.capture("o"), expected)
        inventory.advance(20)
        self.assertEqual(inventory.get("o"), expected)
        self.assertEqual(inventory.stock(), {"tea": 3})

    def test_release_is_idempotent_and_survives_deadline(self):
        inventory = Inventory({"tea": 5})
        inventory.reserve("o", {"tea": 2}, 5)
        expected = self.record("o", {"tea": 2}, 5, "released")
        self.assertEqual(inventory.release("o"), expected)
        self.assertEqual(inventory.release("o"), expected)
        inventory.advance(20)
        self.assertEqual(inventory.get("o"), expected)
        self.assertEqual(inventory.stock(), {"tea": 5})

    def test_expiry_boundary_and_multiple_holds(self):
        inventory = Inventory({"tea": 10, "mug": 4})
        inventory.reserve("early", {"tea": 2, "mug": 1}, 5)
        inventory.reserve("same", {"tea": 1}, 5)
        inventory.reserve("late", {"tea": 3, "mug": 2}, 9)
        self.assertIsNone(inventory.advance(4))
        self.assertEqual(inventory.stock(), {"tea": 4, "mug": 1})
        self.assertEqual(inventory.get("early")["status"], "held")
        self.assertIsNone(inventory.advance(5))
        self.assertEqual(inventory.stock(), {"tea": 7, "mug": 2})
        self.assertEqual(inventory.get("early")["status"], "expired")
        self.assertEqual(inventory.get("same")["status"], "expired")
        self.assertEqual(inventory.get("late")["status"], "held")
        inventory.advance(5)
        self.assertEqual(inventory.stock(), {"tea": 7, "mug": 2})
        inventory.advance(50)
        self.assertEqual(inventory.stock(), {"tea": 10, "mug": 4})
        inventory.advance(60)
        self.assertEqual(inventory.stock(), {"tea": 10, "mug": 4})

    def test_identical_replays_return_current_status(self):
        for status in ("held", "captured", "released", "expired"):
            with self.subTest(status=status):
                inventory = Inventory({"tea": 2, "mug": 1})
                inventory.reserve("o", {"tea": 2, "mug": 1}, 5)
                if status == "captured":
                    inventory.capture("o")
                elif status == "released":
                    inventory.release("o")
                elif status == "expired":
                    inventory.advance(5)
                if status != "held":
                    inventory.advance(10)
                before = inventory.stock()
                self.assertEqual(inventory.reserve("o", {"mug": 1, "tea": 2}, 5),
                                 self.record("o", {"tea": 2, "mug": 1}, 5, status))
                self.assertEqual(inventory.stock(), before)

    def test_conflicting_replays_leave_original_intact(self):
        for status in ("held", "captured", "released", "expired"):
            with self.subTest(status=status):
                inventory = Inventory({"tea": 8, "mug": 3})
                inventory.reserve("o", {"tea": 2}, 5)
                if status == "captured":
                    inventory.capture("o")
                elif status == "released":
                    inventory.release("o")
                elif status == "expired":
                    inventory.advance(5)
                before_stock = inventory.stock()
                before_record = inventory.get("o")
                for items, deadline in (({"tea": 3}, 5), ({"tea": 2, "mug": 1}, 5),
                                        ({"mug": 2}, 5), ({"tea": 2}, 6)):
                    with self.assertRaises(ValueError):
                        inventory.reserve("o", items, deadline)
                    self.assertEqual(inventory.stock(), before_stock)
                    self.assertEqual(inventory.get("o"), before_record)

    def test_terminal_transitions_reject_without_mutation(self):
        for status, operations in (("captured", ("release",)), ("released", ("capture",)),
                                   ("expired", ("capture", "release"))):
            with self.subTest(status=status):
                inventory = Inventory({"tea": 3})
                inventory.reserve("o", {"tea": 2}, 5)
                if status == "expired":
                    inventory.advance(5)
                else:
                    getattr(inventory, "capture" if status == "captured" else "release")("o")
                before_stock = inventory.stock()
                before_record = inventory.get("o")
                for operation in operations:
                    with self.assertRaises(ValueError):
                        getattr(inventory, operation)("o")
                    self.assertEqual(inventory.stock(), before_stock)
                    self.assertEqual(inventory.get("o"), before_record)

    def test_partial_reservation_failure_is_atomic_and_key_stays_unused(self):
        for items, error in (({"tea": 1, "mug": 3}, ValueError),
                             ({"tea": 1, "unknown": 1}, KeyError),
                             ({"tea": 1, "mug": 0}, ValueError)):
            with self.subTest(items=items):
                inventory = Inventory({"tea": 3, "mug": 2})
                with self.assertRaises(error):
                    inventory.reserve("o", items, 5)
                self.assertEqual(inventory.stock(), {"tea": 3, "mug": 2})
                with self.assertRaises(KeyError):
                    inventory.get("o")
                inventory.reserve("o", {"tea": 3, "mug": 2}, 5)
                self.assertEqual(inventory.stock(), {"tea": 0, "mug": 0})

    def test_all_public_records_are_detached_snapshots(self):
        inventory = Inventory({"tea": 9})
        items = {"tea": 2}
        reserve_result = inventory.reserve("o", items, 5)
        items["tea"] = 8
        first_read = inventory.get("o")
        second_read = inventory.get("o")
        first_read["items"]["tea"] = 100
        first_read["status"] = "released"
        self.assertEqual(second_read, self.record("o", {"tea": 2}, 5))
        reserve_result["items"]["tea"] = 0
        reserve_result["key"] = "different"
        self.assertEqual(inventory.get("o"), self.record("o", {"tea": 2}, 5))
        captured = inventory.capture("o")
        captured["items"].clear()
        captured["status"] = "held"
        self.assertEqual(inventory.get("o"), self.record("o", {"tea": 2}, 5, "captured"))
        inventory.reserve("p", {"tea": 3}, 6)
        released = inventory.release("p")
        released["items"]["tea"] = 999
        released["expires_at"] = 100
        self.assertEqual(inventory.get("p"), self.record("p", {"tea": 3}, 6, "released"))
        snapshot = inventory.stock()
        snapshot.clear()
        self.assertEqual(inventory.stock(), {"tea": 7})
        self.assertEqual(second_read["status"], "held")

    def test_constructor_validation(self):
        for initial in (None, [], [("tea", 2)], "tea", {"": 1}, {1: 2},
                        {"tea": -1}, {"tea": True}, {"tea": 1.0}, {"tea": "1"}):
            with self.subTest(initial=initial), self.assertRaises(ValueError):
                Inventory(initial)

    def test_item_validation_and_atomic_restock(self):
        invalid_items = (None, [], [("tea", 2)], {}, {"": 1}, {2: 1},
                         {"tea": 0}, {"tea": -1}, {"tea": True}, {"tea": 1.0},
                         {"tea": "1"}, {"tea": 1, "new": -1}, {"new": 1, "tea": False})
        for items in invalid_items:
            for operation in ("reserve", "restock"):
                with self.subTest(items=items, operation=operation):
                    inventory = Inventory({"tea": 5})
                    inventory.reserve("existing", {"tea": 1}, 5)
                    with self.assertRaises(ValueError):
                        if operation == "reserve":
                            inventory.reserve("o", items, 5)
                        else:
                            inventory.restock(items)
                    self.assertEqual(inventory.stock(), {"tea": 4})
                    self.assertEqual(inventory.get("existing"), self.record("existing", {"tea": 1}, 5))
                    with self.assertRaises(KeyError):
                        inventory.get("o")

    def test_key_validation_and_unknown_keys(self):
        for key in ("", None, 7, True, [], {}):
            for operation in ("reserve", "get", "capture", "release"):
                with self.subTest(key=key, operation=operation):
                    inventory = Inventory({"tea": 2})
                    with self.assertRaises(ValueError):
                        if operation == "reserve":
                            inventory.reserve(key, {"tea": 1}, 5)
                        else:
                            getattr(inventory, operation)(key)
                    self.assertEqual(inventory.stock(), {"tea": 2})
        inventory = Inventory({"tea": 2})
        for operation in ("get", "capture", "release"):
            with self.subTest(operation=operation), self.assertRaises(KeyError):
                getattr(inventory, operation)("missing")
        inventory.reserve("missing", {"tea": 2}, 5)
        self.assertEqual(inventory.stock(), {"tea": 0})

    def test_timestamp_validation_and_clock_failure_atomicity(self):
        inventory = Inventory({"tea": 4})
        inventory.reserve("o", {"tea": 1}, 12)
        inventory.advance(10)
        for now in (-1, 9, True, 10.0, "20", None):
            with self.subTest(now=now), self.assertRaises(ValueError):
                inventory.advance(now)
            self.assertEqual(inventory.get("o")["status"], "held")
            self.assertEqual(inventory.stock(), {"tea": 3})
        for deadline in (-1, 0, 10, True, 11.0, "11", None):
            with self.subTest(deadline=deadline), self.assertRaises(ValueError):
                inventory.reserve("bad", {"tea": 1}, deadline)
            self.assertEqual(inventory.stock(), {"tea": 3})
            with self.assertRaises(KeyError):
                inventory.get("bad")
        inventory.reserve("next", {"tea": 1}, 11)
        inventory.advance(11)
        self.assertEqual(inventory.get("next")["status"], "expired")
        self.assertEqual(inventory.get("o")["status"], "held")
        self.assertEqual(inventory.stock(), {"tea": 3})

    def test_replays_still_validate_values(self):
        inventory = Inventory({"tea": 3})
        inventory.reserve("o", {"tea": 1}, 1)
        for items, deadline in (({"tea": True}, 1), ({"tea": 1.0}, 1),
                                ({"tea": 1}, True), ({"tea": 1}, 1.0)):
            with self.subTest(items=items, deadline=deadline), self.assertRaises(ValueError):
                inventory.reserve("o", items, deadline)
        self.assertEqual(inventory.stock(), {"tea": 2})
        self.assertEqual(inventory.get("o"), self.record("o", {"tea": 1}, 1))

    def test_names_are_exact_and_case_sensitive(self):
        inventory = Inventory({"Tea": 2, "tea": 3, " ": 1})
        inventory.reserve("Order", {"Tea": 1}, 5)
        inventory.reserve("order", {"tea": 2}, 5)
        inventory.reserve(" ", {" ": 1}, 5)
        self.assertEqual(inventory.stock(), {"Tea": 1, "tea": 1, " ": 0})
        inventory.release("order")
        self.assertEqual(inventory.stock(), {"Tea": 1, "tea": 3, " ": 0})
        self.assertEqual(inventory.get("Order")["status"], "held")

    def test_checkout_sequence_with_shared_stock(self):
        inventory = Inventory({"tea": 12, "mug": 4})
        inventory.reserve("alice", {"tea": 3, "mug": 1}, 5)
        inventory.reserve("bob", {"tea": 4}, 9)
        inventory.reserve("carol", {"mug": 2}, 7)
        inventory.capture("alice")
        inventory.release("carol")
        inventory.restock({"tea": 2, "mug": 1})
        inventory.reserve("dana", {"tea": 5, "mug": 3}, 12)
        self.assertEqual(inventory.stock(), {"tea": 2, "mug": 1})
        inventory.advance(9)
        self.assertEqual(inventory.stock(), {"tea": 6, "mug": 1})
        inventory.reserve("bob", {"tea": 4}, 9)
        inventory.release("dana")
        inventory.advance(20)
        self.assertEqual(inventory.stock(), {"tea": 11, "mug": 4})
        self.assertEqual({key: inventory.get(key)["status"] for key in ("alice", "bob", "carol", "dana")},
                         {"alice": "captured", "bob": "expired", "carol": "released", "dana": "released"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
