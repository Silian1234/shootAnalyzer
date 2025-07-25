# ─── image_processor.py ─────────────────────────────────────────────
import numpy as np
from math import atan2, degrees, hypot

# прежние границы (углы) оставляем
_BOUNDARIES = {
    2: (202.5, 247.5),   # ↙︎  левый‑нижний
    3: (157.5, 202.5),   # ←   левый
    4: (112.5, 157.5),   # ↖︎  левый‑верхний
    5: ( 67.5, 112.5),   # ↑   верхний‑по‑центру
    6: ( 22.5,  67.5),   # ↗︎  правый‑верхний
    7: (-22.5,  22.5),   # →   правый
    8: (-67.5, -22.5),   # ↘︎  правый‑нижний
    9: (-112.5,-67.5),   # ↓   нижний‑по‑центру
}

CENTER_R_REL = 0.20      # 20 % от min(H, W) ⇒ довольно щедрый «яблочко»

def _angle_deg(dx: float, dy: float) -> float:
    """угол [‑180;+180] в градусах, 0° — вправо, CCW +"""
    return degrees(atan2(dy, dx))

def _sector(angle: float) -> str:
    for sec, (amin, amax) in _BOUNDARIES.items():
        if amin <= angle <= amax:
            return str(sec)
    return "9"            # fallback: точно где‑то снизу

def determine_zones(hits: list[tuple[int,int]], img: np.ndarray) -> list[str]:
    h, w = img.shape[:2]
    cx, cy      = w / 2, h / 2
    r_center_px = min(h, w) * CENTER_R_REL

    zones: list[str] = []
    for x, y in hits:
        dx, dy = x - cx, cy - y          # y переворачиваем (вверх +)
        if hypot(dx, dy) <= r_center_px:
            zones.append("1")
        else:
            zones.append(_sector(_angle_deg(dx, dy)))
    return zones
