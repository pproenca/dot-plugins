import math
import unittest

from dispatch import Queue


class QueueContract(unittest.TestCase):
    def test_empty_and_future(self):
        q = Queue()
        self.assertIsNone(q.claim(0, 5))
        self.assertTrue(q.schedule('a', {'v': 1}, 10))
        self.assertIsNone(q.claim(9, 5))
        self.assertEqual(q.claim(10, 5)['key'], 'a')

    def test_order_and_no_live_double_claim(self):
        q = Queue()
        for key, due in [('a', 5), ('b', 2), ('c', 2)]:
            q.schedule(key, key, due)
        self.assertEqual([q.claim(5, 20)['key'] for _ in range(3)], ['b', 'c', 'a'])
        self.assertIsNone(q.claim(6, 1))

    def test_duplicate_schedule_does_not_reschedule_or_reopen(self):
        q = Queue()
        q.schedule('a', [1], 5)
        self.assertFalse(q.schedule('a', [1], -10))
        self.assertIsNone(q.claim(4, 1))
        lease = q.claim(5, 2)
        self.assertFalse(q.schedule('a', [1], 0))
        self.assertIsNone(q.claim(6, 1))
        self.assertTrue(q.ack(lease['token'], 6))
        self.assertFalse(q.schedule('a', [1], 0))
        self.assertIsNone(q.claim(20, 1))

    def test_payload_conflict_is_atomic(self):
        q = Queue()
        q.schedule('a', {'v': 1}, 5)
        with self.assertRaises(ValueError):
            q.schedule('a', {'v': 2}, 0)
        self.assertIsNone(q.claim(4, 1))
        self.assertEqual(q.claim(5, 1)['payload'], {'v': 1})

    def test_payload_copies_at_both_boundaries(self):
        q = Queue()
        payload = {'nested': [1]}
        q.schedule('a', payload, 0)
        payload['nested'].append(2)
        lease = q.claim(0, 1)
        self.assertEqual(lease['payload'], {'nested': [1]})
        lease['payload']['nested'].append(3)
        again = q.claim(1, 1)
        self.assertEqual(again['payload'], {'nested': [1]})
        self.assertFalse(q.schedule('a', {'nested': [1]}, 0))

    def test_expiry_boundary_and_fresh_tokens(self):
        q = Queue()
        q.schedule('a', None, 0)
        first = q.claim(0, 5)
        self.assertIsInstance(first['token'], str)
        self.assertTrue(first['token'])
        self.assertFalse(q.ack(first['token'], 5))
        self.assertFalse(q.retry(first['token'], 5, 99))
        second = q.claim(5, 5)
        self.assertNotEqual(first['token'], second['token'])
        self.assertFalse(q.ack(first['token'], 6))
        self.assertTrue(q.ack(second['token'], 6))
        self.assertFalse(q.ack(second['token'], 6))
        self.assertIsNone(q.claim(100, 1))

    def test_retry_preserves_insertion_order_and_invalidates_token(self):
        q = Queue()
        q.schedule('a', 1, 0)
        q.schedule('b', 2, 5)
        first = q.claim(0, 10)
        self.assertTrue(q.retry(first['token'], 1, 5))
        self.assertFalse(q.ack(first['token'], 2))
        self.assertFalse(q.retry(first['token'], 2, 0))
        self.assertIsNone(q.claim(4, 1))
        self.assertEqual(q.claim(5, 5)['key'], 'a')
        self.assertEqual(q.claim(5, 5)['key'], 'b')

    def test_expired_and_queued_jobs_share_due_order(self):
        q = Queue()
        q.schedule('a', 1, 0)
        q.schedule('b', 2, 1)
        first = q.claim(0, 2)
        self.assertEqual(q.claim(2, 5)['key'], 'a')
        self.assertEqual(q.claim(2, 5)['key'], 'b')
        self.assertFalse(q.retry(first['token'], 2, -100))

    def test_invalid_time_inputs_do_not_mutate(self):
        bad_times = [True, False, None, '1', math.inf, -math.inf, math.nan]
        for bad in bad_times:
            with self.subTest(value=repr(bad)):
                q = Queue()
                with self.assertRaises(ValueError):
                    q.schedule('a', 1, bad)
                self.assertTrue(q.schedule('a', 2, 0))
                with self.assertRaises(ValueError):
                    q.claim(bad, 5)
                with self.assertRaises(ValueError):
                    q.claim(0, bad)
                token = q.claim(0, 5)['token']
                with self.assertRaises(ValueError):
                    q.ack(token, bad)
                with self.assertRaises(ValueError):
                    q.retry(token, 1, bad)
                self.assertTrue(q.ack(token, 1))

    def test_invalid_duration_does_not_lease(self):
        q = Queue()
        q.schedule('a', 1, 0)
        for duration in [0, -1]:
            with self.assertRaises(ValueError):
                q.claim(0, duration)
        self.assertEqual(q.claim(0, 1)['key'], 'a')

    def test_invalid_json_and_key_rejected(self):
        for payload in [{1: 'x'}, {'a': math.nan}, {1, 2}, object(), (1, 2)]:
            q = Queue()
            with self.subTest(payload=repr(payload)):
                with self.assertRaises(ValueError):
                    q.schedule('a', payload, 0)
                self.assertIsNone(q.claim(0, 1))
        for key in ['', None, 1, True]:
            with self.subTest(key=repr(key)):
                with self.assertRaises(ValueError):
                    Queue().schedule(key, None, 0)

    def test_unknown_tokens_are_noops(self):
        q = Queue()
        q.schedule('a', 1, 0)
        for token in ['missing', None, [], 0]:
            self.assertFalse(q.ack(token, 0))
            self.assertFalse(q.retry(token, 0, 10))
        self.assertEqual(q.claim(0, 1)['key'], 'a')


if __name__ == '__main__':
    unittest.main()
