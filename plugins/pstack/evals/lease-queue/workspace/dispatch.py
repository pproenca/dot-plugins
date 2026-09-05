class Queue:
    def schedule(self, key, payload, due):
        raise NotImplementedError

    def claim(self, now, lease_seconds):
        raise NotImplementedError

    def ack(self, token, now):
        raise NotImplementedError

    def retry(self, token, now, due):
        raise NotImplementedError
