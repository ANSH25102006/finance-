# ============================================================
#  detector_registry.py — Auto-registration of all detectors
# ============================================================

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.financial_intelligence.detector_base import BaseDetector

logger = logging.getLogger(__name__)


class DetectorRegistry:
    """
    Singleton registry that holds all detector instances.

    Detectors are registered on import via `register()`.
    The engine iterates `registry.detectors` to run them all —
    it never calls individual detectors by name.

    Usage
    -----
    >>> registry = DetectorRegistry.get_instance()
    >>> registry.register(MyDetector())
    >>> for detector in registry.detectors:
    ...     insights = detector.detect(ctx)
    """

    _instance: DetectorRegistry | None = None

    def __init__(self) -> None:
        self._detectors: list[BaseDetector] = []

    @classmethod
    def get_instance(cls) -> DetectorRegistry:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ------------------------------------------------------------------ #

    def register(self, detector: BaseDetector) -> None:
        """Add a detector to the registry."""
        self._detectors.append(detector)
        logger.debug("Registered detector: %s", detector.name)

    @property
    def detectors(self) -> list[BaseDetector]:
        """Return the ordered list of registered detectors (read-only view)."""
        return list(self._detectors)

    def clear(self) -> None:
        """Remove all registered detectors (useful for testing)."""
        self._detectors.clear()

    def __len__(self) -> int:
        return len(self._detectors)

    def __repr__(self) -> str:
        names = [d.name for d in self._detectors]
        return f"DetectorRegistry({names})"


# ------------------------------------------------------------------ #
# Module-level singleton — imported by detectors and the engine
# ------------------------------------------------------------------ #
registry = DetectorRegistry.get_instance()
