from typing import Any, Optional


class NullClient:
    def __init__(self, event_id: Optional[int] = None):
        self.event_id: int = event_id if event_id is not None else 0

    def emit(self, *args: Any, **kwargs: Any) -> int:
        self.event_id += 1
        return self.event_id

    def emit_grpc(self, *args: Any, **kwargs: Any) -> int:
        return self.emit(*args, **kwargs)

    def get_event(self, *args: Any, **kwargs: Any) -> None:
        return None

    def children(self, *args: Any, **kwargs: Any) -> list[int]:
        return []

    def ancestors(self, *args: Any, **kwargs: Any) -> list[int]:
        return []

    def descendants(self, *args: Any, **kwargs: Any) -> None:
        return None

    def descendants_batch(self, *args: Any, **kwargs: Any) -> None:
        return None

    def provenance(self, *args: Any, **kwargs: Any) -> None:
        return None

    def provenance_batch(self, *args: Any, **kwargs: Any) -> None:
        return None

    def roots(self) -> list[int]:
        return []

    def heads(self) -> list[int]:
        return []

    def snapshot(self) -> dict[str, Any]:
        return {}

    def health(self) -> bool:
        return True

    def version(self) -> dict[str, Any]:
        return {}

    def subscribe(self, *args: Any, **kwargs: Any) -> None:
        return None
