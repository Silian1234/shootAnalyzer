from __future__ import annotations

from math import atan2, degrees
from dataclasses import dataclass
from typing import List, Tuple

# Границы секторов 2–9 в градусах (0° — вправо, +CCW)
_BOUNDARIES = {
    2: (202.5, 247.5),
    3: (157.5, 202.5),
    4: (112.5, 157.5),
    5: ( 67.5, 112.5),
    6: ( 22.5,  67.5),
    7: (-22.5,  22.5),
    8: (-67.5, -22.5),
    9: (-112.5,-67.5),
}

@dataclass
class Hit:
    x_px: float
    y_px: float
    sector: str

def _angle_deg(x: float, y: float) -> float:
    return degrees(atan2(y, x))

def _sector_for_angle(angle: float) -> str | None:
    for sec, (a_min, a_max) in _BOUNDARIES.items():
        if a_min <= angle <= a_max:
            return str(sec)
    return None

def classify_hits(points_px: List[Tuple[float, float]]) -> List[Hit]:
    """
    Принимает список (x, y) в пикселях, где (0,0) — центр листа, y растёт вверх.
    Возвращает Hit(x, y, sector) только для секторов 2–9.
    """
    hits: List[Hit] = []
    for x, y in points_px:
        ang = _angle_deg(x, -y)
        sec = _sector_for_angle(ang)
        if sec:
            hits.append(Hit(x, y, sec))
    return hits
