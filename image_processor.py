import numpy as np
from math import atan2, degrees, hypot

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

CENTER_R_REL = 0.20

def _angle_deg(dx: float, dy: float) -> float:
    return degrees(atan2(dy, dx))

def _sector(angle: float) -> str:
    for sec, (amin, amax) in _BOUNDARIES.items():
        if amin <= angle <= amax:
            return str(sec)
    return "9"

def determine_zones(hits: list[tuple[int,int]], img: np.ndarray) -> list[str]:
    h, w = img.shape[:2]
    cx, cy      = w / 2, h / 2
    r_center_px = min(h, w) * CENTER_R_REL

    zones: list[str] = []
    for x, y in hits:
        dx, dy = x - cx, cy - y
        if hypot(dx, dy) <= r_center_px:
            zones.append("1")
        else:
            zones.append(_sector(_angle_deg(dx, dy)))
    return zones
