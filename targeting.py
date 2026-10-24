"""Target selection (nearest / specific / sticky) and the simulated aim pull."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional, Sequence

from config import AimConfig, AimMode, NEAREST
from targets import SimTarget
from vector_math import Vector2


class TargetSelector:
    def __init__(self, config: AimConfig):
        self.config = config
        self.locked_id: Optional[int] = None
        config.subscribe(self._on_config)

    def _on_config(self, cfg: AimConfig, changed: dict) -> None:
        # Switching target or mode drops any sticky lock.
        if "target_choice" in changed or "mode" in changed or "enabled" in changed:
            self.release()

    def release(self) -> None:
        self.locked_id = None

    def select(self, crosshair: Vector2, targets: Sequence[SimTarget]) -> Optional[SimTarget]:
        alive = [t for t in targets if t.alive]
        cfg = self.config

        if cfg.mode == AimMode.STICKY and self.locked_id is not None:
            locked = next((t for t in alive if t.id == self.locked_id), None)
            if locked is not None:
                return locked          # keep it, even outside the FOV
            self.locked_id = None      # it disappeared

        candidate = self._pick(crosshair, alive)
        if cfg.mode == AimMode.STICKY and candidate is not None:
            self.locked_id = candidate.id
        return candidate

    def _pick(self, crosshair: Vector2, alive: Sequence[SimTarget]) -> Optional[SimTarget]:
        in_fov = [(crosshair.distance_to(t.pos), t) for t in alive]
        in_fov = [(d, t) for d, t in in_fov if d <= self.config.fov_radius]
        if not in_fov:
            return None
        if self.config.target_choice == NEAREST:
            return min(in_fov, key=lambda p: p[0])[1]
        for _, t in in_fov:
            if t.name == self.config.target_choice:
                return t
        return None


@dataclass
class AimResult:
    target: Optional[SimTarget] = None
    delta: Vector2 = field(default_factory=Vector2)
    locked: bool = False


class AimController:
    """Computes how far the simulated crosshair should be pulled this frame."""

    def __init__(self, config: AimConfig):
        self.config = config
        self.selector = TargetSelector(config)

    def _rate(self, dist: float) -> float:
        cfg = self.config
        base = 60.0 / (1.0 + cfg.smoothing * 0.5)
        if cfg.mode == AimMode.PRECISION:
            # Gentle far away, stronger as the crosshair closes in.
            prox = max(0.0, min(1.0, 1.0 - dist / cfg.fov_radius))
            return base * (0.35 + 1.65 * prox)
        return base

    def step(self, crosshair: Vector2, targets: Sequence[SimTarget], dt: float) -> AimResult:
        cfg = self.config
        if not cfg.enabled:
            return AimResult()

        target = self.selector.select(crosshair, targets)
        if target is None:
            return AimResult()

        error = target.pos - crosshair
        dist = error.Magnitude
        if cfg.smoothing <= 0:
            alpha = 1.0
        else:
            alpha = 1.0 - math.exp(-self._rate(dist) * dt)
        if cfg.mode == AimMode.PRECISION and dist < 1.5:
            alpha = 0.0  # small deadzone, avoids jitter on the center

        locked = self.selector.locked_id == target.id
        return AimResult(target=target, delta=error * alpha, locked=locked)
