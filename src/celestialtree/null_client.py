from multiprocessing import Value as MPValue


class NullClient:
    def __init__(self, event_id=None):
        self.event_id = event_id if event_id is not None else MPValue("i", 0)

    def emit(self, *args, **kwargs):
        with self.event_id.get_lock():
            self.event_id.value += 1
            return self.event_id.value
        
    def emit_grpc(self, *args, **kwargs):
        return self.emit(*args, **kwargs)

    def get_event(self, *args, **kwargs):
        return None

    def children(self, *args, **kwargs):
        return []

    def ancestors(self, *args, **kwargs):
        return []

    def descendants(self, *args, **kwargs):
        return None

    def descendants_batch(self, *args, **kwargs):
        return None

    def provenance(self, *args, **kwargs):
        return None

    def provenance_batch(self, *args, **kwargs):
        return None

    def heads(self):
        return []

    def subscribe(self, *args, **kwargs):
        return None
