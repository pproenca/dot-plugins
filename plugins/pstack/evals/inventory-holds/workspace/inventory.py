class Inventory:
    def __init__(self, initial_stock):
        self._stock = dict(initial_stock)

    def stock(self):
        return dict(self._stock)

    def restock(self, items):
        raise NotImplementedError

    def reserve(self, key, items, expires_at):
        raise NotImplementedError

    def get(self, key):
        raise NotImplementedError

    def capture(self, key):
        raise NotImplementedError

    def release(self, key):
        raise NotImplementedError

    def advance(self, now):
        raise NotImplementedError
