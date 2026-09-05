"""Contract probes added after the first blinded review, kept separate from its frozen checks."""

import unittest

from dispatch import Queue


class QueueBoundaryContract(unittest.TestCase):
    def test_valid_deep_payload_can_be_scheduled_and_claimed(self):
        payload = 0
        for _ in range(1100):
            payload = [payload]
        q = Queue()
        self.assertTrue(q.schedule('deep', payload, 0))
        returned = q.claim(0, 5)['payload']
        self.assertIsNot(returned, payload)
        for _ in range(1100):
            self.assertIsInstance(returned, list)
            self.assertEqual(len(returned), 1)
            returned = returned[0]
        self.assertEqual(returned, 0)

    def test_finite_arguments_do_not_require_a_finite_float_sum(self):
        q = Queue()
        q.schedule('large', None, 0)
        lease = q.claim(1e308, 1e308)
        self.assertEqual(lease['key'], 'large')
        self.assertTrue(q.ack(lease['token'], 1e308))


if __name__ == '__main__':
    unittest.main()
