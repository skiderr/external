from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Vector2:
    X: float = 0.0
    Y: float = 0.0

    def __add__(self, o: "Vector2") -> "Vector2":
        return Vector2(self.X + o.X, self.Y + o.Y)

    def __sub__(self, o: "Vector2") -> "Vector2":
        return Vector2(self.X - o.X, self.Y - o.Y)

    def __mul__(self, s: float) -> "Vector2":
        return Vector2(self.X * s, self.Y * s)

    __rmul__ = __mul__

    @property
    def Magnitude(self) -> float:
        return math.hypot(self.X, self.Y)

    def distance_to(self, o: "Vector2") -> float:
        return (self - o).Magnitude

    def rotated(self, radians: float) -> "Vector2":
        c, s = math.cos(radians), math.sin(radians)
        return Vector2(self.X * c - self.Y * s, self.X * s + self.Y * c)

    def clamped(self, min_x: float, min_y: float, max_x: float, max_y: float) -> "Vector2":
        return Vector2(min(max(self.X, min_x), max_x), min(max(self.Y, min_y), max_y))


@dataclass(frozen=True)
class Vector3:
    X: float
    Y: float
    Z: float

    def __add__(self, o: "Vector3") -> "Vector3":
        return Vector3(self.X + o.X, self.Y + o.Y, self.Z + o.Z)

    def __sub__(self, o: "Vector3") -> "Vector3":
        return Vector3(self.X - o.X, self.Y - o.Y, self.Z - o.Z)

    def __mul__(self, s: float) -> "Vector3":
        return Vector3(self.X * s, self.Y * s, self.Z * s)

    __rmul__ = __mul__

    @property
    def Magnitude(self) -> float:
        return math.sqrt(self.X ** 2 + self.Y ** 2 + self.Z ** 2)
