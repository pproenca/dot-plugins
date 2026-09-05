import unittest

from inventory import Inventory


class InventorySmoke(unittest.TestCase):
    def test_initial_stock(self):
        self.assertEqual(Inventory({"tea": 5, "mug": 0}).stock(), {"tea": 5, "mug": 0})

    def test_stock_is_a_snapshot(self):
        inventory = Inventory({"tea": 5})
        snapshot = inventory.stock()
        snapshot["tea"] = 0
        self.assertEqual(inventory.stock(), {"tea": 5})


if __name__ == "__main__":
    unittest.main()
