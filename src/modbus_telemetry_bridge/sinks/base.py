from __future__ import annotations

from typing import Protocol

from ..mapping import TagSample


class Sink(Protocol):
    def publish(self, samples: list[TagSample]) -> None:
        ...

    def close(self) -> None:
        ...
