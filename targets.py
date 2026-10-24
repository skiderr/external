"""Simulated targets that bounce around a 2D arena, expire, and respawn."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import List, Optional

from vector_math import Vector2


@dataclass
class SimTarget:
    id: int
    name: str
    pos: Vector2 = field(default_factory=Vector2)
    vel: Vector2 = field(default_factory=Vector2)
    radius: float = 18.0
    alive: bool = True
    ttl: float = 10.0          # seconds until it disappears
    respawn_in: float = 0.0    # countdown while dead


class TargetField:
    def __init__(self, width: int, height: int, count: int = 6, seed: Optional[int] = None):
        self.width = width
        self.height = height
        self.rng = random.Random(seed)
        self.targets: List[SimTarget] = []
        for i in range(count):
            t = SimTarget(id=i + 1, name=f"Target {i + 1}")
            self._spawn(t)
            t.ttl = self.rng.uniform(4.0, 16.0)  # stagger so they don't all vanish together
            self.targets.append(t)

    @property
    def names(self) -> List[str]:
        return [t.name for t in self.targets]

    def alive_targets(self) -> List[SimTarget]:
        return [t for t in self.targets if t.alive]

    def kill(self, t: SimTarget) -> None:
        t.alive = False
        t.respawn_in = self.rng.uniform(1.0, 2.5)

    def _spawn(self, t: SimTarget) -> None:
        m = t.radius + 10
        t.pos = Vector2(self.rng.uniform(m, self.width - m), self.rng.uniform(m, self.height - m))
        ang = self.rng.uniform(0, math.tau)
        speed = self.rng.uniform(70, 170)
        t.vel = Vector2(math.cos(ang) * speed, math.sin(ang) * speed)
        t.ttl = self.rng.uniform(8.0, 16.0)
        t.alive = True

    def update(self, dt: float) -> None:
        for t in self.targets:
            if not t.alive:
                t.respawn_in -= dt
                if t.respawn_in <= 0:
                    self._spawn(t)
                continue

            t.ttl -= dt
            if t.ttl <= 0:
                self.kill(t)
                continue

            if self.rng.random() < dt * 0.6:  # occasional direction change
                t.vel = t.vel.rotated(self.rng.uniform(-0.8, 0.8))

            m = t.radius
            x = t.pos.X + t.vel.X * dt
            y = t.pos.Y + t.vel.Y * dt
            vx, vy = t.vel.X, t.vel.Y
            if x < m:
                x, vx = m, abs(vx)
            elif x > self.width - m:
                x, vx = self.width - m, -abs(vx)
            if y < m:
                y, vy = m, abs(vy)
            elif y > self.height - m:
                y, vy = self.height - m, -abs(vy)
            t.pos = Vector2(x, y)
            t.vel = Vector2(vx, vy)
