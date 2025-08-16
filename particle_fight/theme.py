# theme.py
from typing import Tuple

RGB  = Tuple[int, int, int]
RGBA = Tuple[int, int, int, int]

NEON = {
    "bg": (8, 10, 16),
    "wall_full": (38, 48, 66),
    "wall_broken": (230, 60, 60),
    "hud": (235, 240, 255),
    "species": [
        (0, 255, 200),   # cyan
        (255, 80, 160),  # magenta
        (160, 255, 60),  # lime
        (255, 190, 0),   # amber
    ],
    "special": {
        "crit": (255, 240, 120),
        "shock": (255, 255, 255),
        "trail": (255, 255, 255, 24),  # low-alpha
    },
}

def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * max(0.0, min(1.0, t))

def lerp_color(c1: RGB, c2: RGB, t: float) -> RGB:
    return (int(lerp(c1[0], c2[0], t)),
            int(lerp(c1[1], c2[1], t)),
            int(lerp(c1[2], c2[2], t)))

def wall_color(hp: int, max_hp: int, pal=NEON) -> RGB:
    # 0 hp -> wall_broken, full hp -> wall_full
    t = 1.0 - (max(0, min(max_hp, hp)) / max(1, max_hp))
    return lerp_color(pal["wall_full"], pal["wall_broken"], t)

def species_color(i: int, pal=NEON) -> RGB:
    return pal["species"][i % len(pal["species"])]
