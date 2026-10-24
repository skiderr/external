"""Settings for the aim trainer. GUI widgets write here, the simulation reads here."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, List

NEAREST = "Nearest"


class AimMode(str, Enum):
    SMOOTH = "Smooth"
    PRECISION = "Precision"
    STICKY = "Sticky Target"


Listener = Callable[["AimConfig", dict], None]


@dataclass
class AimConfig:
    enabled: bool = True
    fov_radius: float = 150.0      # pixels
    smoothing: float = 12.0        # 0 = instant, higher = slower
    mode: AimMode = AimMode.SMOOTH
    target_choice: str = NEAREST   # NEAREST or a target name
    show_fov: bool = True

    _listeners: List[Listener] = field(default_factory=list, repr=False, compare=False)

    # ---- limits ----
    FOV_MIN = 20.0
    FOV_MAX = 450.0
    SMOOTH_MIN = 0.0
    SMOOTH_MAX = 50.0

    def subscribe(self, fn: Listener) -> None:
        self._listeners.append(fn)

    def update(self, **changes: Any) -> None:
        """Apply changes immediately and notify listeners with only what changed."""
        changed: dict = {}
        for key, value in changes.items():
            if key.startswith("_") or not hasattr(self, key):
                raise AttributeError(f"Unknown setting: {key}")
            if key == "mode" and not isinstance(value, AimMode):
                value = AimMode(value)
            elif key == "fov_radius":
                value = max(self.FOV_MIN, min(self.FOV_MAX, float(value)))
            elif key == "smoothing":
                value = max(self.SMOOTH_MIN, min(self.SMOOTH_MAX, float(value)))
            if getattr(self, key) != value:
                setattr(self, key, value)
                changed[key] = value
        if changed:
            for fn in list(self._listeners):
                fn(self, changed)
