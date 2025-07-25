from __future__ import annotations
import cv2
import numpy as np
from typing import Iterable, Tuple

# ---------- служебные ---------------------------------------------------


def _ensure_bgr(img: np.ndarray) -> np.ndarray:
    """Гарантируем BGR‑uint8."""
    if img.dtype != np.uint8:
        img = (np.clip(img, 0, 1) * 255).astype(np.uint8)
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    elif img.shape[2] == 4:
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    return img


# ---------- сетка -------------------------------------------------------


def draw_sector_grid(
    img: np.ndarray,
    *,
    center: Tuple[int, int] | None = None,
    radius: int | None = None,
    color: Tuple[int, int, int] = (0, 140, 255),
    thickness: int = 2,
    draw_center: bool = False,
) -> np.ndarray:
    vis = _ensure_bgr(img.copy())
    h, w = vis.shape[:2]
    cx, cy = center if center else (w // 2, h // 2)
    r = radius if radius else int(min(h, w) * 0.48)

    # радиальные лучи
    for k in range(8):
        ang = np.deg2rad(k * 45)
        x2 = int(cx + r * np.cos(ang))
        y2 = int(cy + r * np.sin(ang))
        cv2.line(vis, (cx, cy), (x2, y2), color, thickness)

    if draw_center:
        cv2.circle(vis, (cx, cy), int(r * 0.20), color, thickness)

    label_r = int(r * 0.82)
    sector_labels = ["2", "3", "4", "5", "6", "7", "8", "9"]
    for idx, ang_deg in enumerate(range(-112, 248, 45)):
        ang = np.deg2rad(ang_deg)
        lx = int(cx + label_r * np.cos(ang))
        ly = int(cy + label_r * np.sin(ang))
        cv2.putText(
            vis,
            sector_labels[idx],
            (lx - 10, ly + 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            color,
            2,
            cv2.LINE_AA,
        )
    return vis


def mark_hits(
    img: np.ndarray,
    hits: Iterable[Tuple[int, int]],
    dot_color: Tuple[int, int, int] = (0, 0, 255),
) -> np.ndarray:
    """Наносит сетку + точки попаданий."""
    vis = draw_sector_grid(img)
    for idx, (x, y) in enumerate(hits, 1):
        cv2.circle(vis, (x, y), 6, dot_color, -1, cv2.LINE_AA)
        cv2.putText(
            vis,
            str(idx),
            (x + 8, y - 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            dot_color,
            2,
            cv2.LINE_AA,
        )
    return vis
