import unittest

from dispatch import Queue


class QueueSmoke(unittest.TestCase):
    def test_create_queue(self):
        self.assertIsInstance(Queue(), Queue)


if __name__ == '__main__':
    unittest.main()
