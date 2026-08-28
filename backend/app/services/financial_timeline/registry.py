# ============================================================
#  registry.py — Singleton registry for timeline event builders
# ============================================================

from typing import TypeVar, Type

from app.services.financial_timeline.event_base import BaseEventBuilder

T = TypeVar("T", bound=BaseEventBuilder)

class EventBuilderRegistry:
    """Singleton registry holding all event builders."""

    def __init__(self) -> None:
        self.builders: list[BaseEventBuilder] = []
        self._registered_types: set[Type[BaseEventBuilder]] = set()

    def register(self, builder: BaseEventBuilder) -> None:
        """Register a builder instance if its type hasn't been registered yet."""
        builder_type = type(builder)
        if builder_type not in self._registered_types:
            self.builders.append(builder)
            self._registered_types.add(builder_type)

    def clear(self) -> None:
        """Clear all registered builders (useful for tests)."""
        self.builders.clear()
        self._registered_types.clear()

registry = EventBuilderRegistry()
