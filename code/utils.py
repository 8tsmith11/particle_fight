import random
import pygame
import rules
from particle import Particle

walls = None
particles = None
tile_size = 0

# Creates a box of walls with corners (x1, y1), (x2, y2) in grid coordinates
def wall_box(x1, y1, x2, y2, filled=False):
    if filled:
        for y in range(min(y1, y2), max(y1, y2) + 1):
            for x in range(min(x1, x2), max(x1, x2) + 1): 
                if 0 <= y < len(walls) and 0 <= x < len(walls[0]):
                    walls[y][x] = rules.WALL_HEALTH
    else:
        for x in range(x1, x2 + 1):
            walls[y1][x] = rules.WALL_HEALTH
            walls[y2][x] = rules.WALL_HEALTH
        for y in range(y1, y2 + 1):
            walls[y][x1] = rules.WALL_HEALTH
            walls[y][x2] = rules.WALL_HEALTH

# spawn count particles in the boxed region, pixel coordinates, inclusive
def spawn_particles_pixels(x1, y1, x2, y2, count, radius = 1, **kwargs):
    for _ in range(count):
        x = random.uniform(min(x1, x2), max(x1, x2))
        y = random.uniform(min(y1, y2), max(y1, y2))
        while intersects_wall(x, y, radius):
            x = random.uniform(min(x1, x2), max(x1, x2))
            y = random.uniform(min(y1, y2), max(y1, y2))

        pos = pygame.Vector2(x, y)
        particle = Particle(pos, radius=radius, **kwargs)
        particles.append(particle)


def intersects_wall(x, y, radius):
    if walls is None or tile_size <= 0: # uninitialized world
        return False
    
    # Possible tiles to intersect
    left   = max(0, int((x - radius) // tile_size))
    right  = min(len(walls[0]) - 1, int((x + radius) // tile_size))
    top    = max(0, int((y - radius) // tile_size))
    bottom = min(len(walls) - 1, int((y + radius) // tile_size))

    r2 = radius * radius
    for ty in range(top, bottom + 1):
        for tx in range(left, right + 1):
            if walls[ty][tx] <= 0:
                continue

            rect_l = tx * tile_size
            rect_t = ty * tile_size
            rect_r = rect_l + tile_size
            rect_b = rect_t + tile_size

            # closest point on tile to circle center
            nearest_x = max(rect_l, min(x, rect_r))
            nearest_y = max(rect_t, min(y, rect_b))

            dx = x - nearest_x
            dy = y - nearest_y

            if dx*dx + dy*dy < r2:
                return True
    return False

# spawn count particles in the boxed region, grid coordinates, inclusive
def spawn_particles_grid(x1, y1, x2, y2, count, **kwargs):
    x1 *= tile_size
    y1 *= tile_size
    x2 *= tile_size
    y2 *= tile_size
    spawn_particles_pixels(x1, y1, x2, y2, count, **kwargs)

def wall_grid(x1, y1, x2, y2, rows, cols, border=False):
    if border:
        wall_box(x1, y1, x2, y2)

    row_size = (y2 - y1) // rows
    col_size = (x2 - x1) // cols

    for i in range(1, rows):
        wall_box(x1, y1 + row_size * i, x2, y1 + row_size * i)
    for i in range(1, cols):
        wall_box(x1 + col_size * i, y1, x1 + col_size * i, y2)
    
def sum_kinetic_energy(particles):
    sum = 0
    for p in particles:
        sum += p.get_kinetic_energy()
    return sum

def sum_potential_energy(particles):
    sum = 0
    for p in particles:
        sum += p.get_potential_energy()
    return sum

def sum_total_energy(particles):
    sum = 0
    for p in particles:
        sum += p.get_total_energy()
    return sum

def wall_quad_concentric(
    rows_per_quad: int = 2,
    cols_per_quad: int = 2,
    *,
    thickness: int = 1,   # wall thickness in tiles (centered on lines)
    rings: int = 1,       # extra concentric boxes inside each cell
    ring_step: int = 2,   # spacing between rings in tiles
    reset: bool = True    # clear all walls before building
):
    """
    Build a 'quad-concentric' arena:
      - Outer border box
      - Central cross splitting the map into 4 quadrants
      - In each quadrant: a rows_per_quad x cols_per_quad grid (no doors)
      - Optional concentric rings inside each cell (no doors)

    Returns: list of cell interiors as (cx1, cy1, cx2, cy2) in TILE COORDS (inclusive).
             These are the *open* areas where you can spawn particles.

    Notes:
      - Uses global `walls` and `rules.WALL_HEALTH`
      - Coordinates here are in *grid tiles*, not pixels.
    """
    assert walls is not None and len(walls) and len(walls[0]), "utils.walls must be initialized"
    H, W = len(walls), len(walls[0])
    rows_per_quad = max(1, int(rows_per_quad))
    cols_per_quad = max(1, int(cols_per_quad))
    thickness = max(1, int(thickness))
    rings = max(0, int(rings))
    ring_step = max(1, int(ring_step))

    # helpers ---------------------------------------------------
    def _clear_all():
        for ty in range(H):
            for tx in range(W):
                walls[ty][tx] = 0

    # draw a vertical line of thickness, centered on x
    def _thick_vline(x, y1, y2, t):
        half = t // 2
        for dx in range(-half, t - half):
            wall_box(max(0, x + dx), max(0, y1), min(W-1, x + dx), min(H-1, y2))

    # draw a horizontal line of thickness, centered on y
    def _thick_hline(x1, x2, y, t):
        half = t // 2
        for dy in range(-half, t - half):
            wall_box(max(0, x1), max(0, y + dy), min(W-1, x2), min(H-1, y + dy))

    # integer linspace to avoid drift
    def _splits(a, b, n_segments):
        return [int(round(a + (b - a) * i / n_segments)) for i in range(n_segments + 1)]

    def _cell_interiors_from_grid(x1, y1, x2, y2, r, c, t):
        """Return interiors for an rxc grid bounded by [x1..x2],[y1..y2] (tile coords)."""
        xs = _splits(x1, x2, c)
        ys = _splits(y1, y2, r)
        cells = []
        for ri in range(r):
            for ci in range(c):
                L, R = xs[ci], xs[ci+1]
                T, B = ys[ri], ys[ri+1]
                # Shrink by thickness on all sides so we don't spawn inside walls
                cx1, cy1 = L + t, T + t
                cx2, cy2 = R - t, B - t
                if cx2 > cx1 and cy2 > cy1:
                    cells.append((cx1, cy1, cx2, cy2))
        return cells

    # build -----------------------------------------------------
    if reset:
        _clear_all()

    # outer border
    wall_box(0, 0, W-1, H-1)

    # center cross
    midx, midy = W // 2, H // 2
    _thick_vline(midx, 1, H-2, thickness)
    _thick_hline(1, W-2, midy, thickness)

    # quadrant bounds (exclusive of cross lines)
    quads = [
        (0,       0,       midx-1, midy-1),      # TL
        (midx+1,  0,       W-1,     midy-1),      # TR
        (0,       midy+1,  midx-1,  H-1),         # BL
        (midx+1,  midy+1,  W-1,     H-1),         # BR
    ]

    all_cells = []

    for (qx1, qy1, qx2, qy2) in quads:
        if qx2 - qx1 < 2 or qy2 - qy1 < 2:
            continue

        # draw quadrant border so each quadrant is sealed on its own
        wall_box(qx1, qy1, qx2, qy2)

        # internal grid lines inside the quadrant
        xs = _splits(qx1, qx2, cols_per_quad)
        ys = _splits(qy1, qy2, rows_per_quad)

        # vertical grid walls (skip outermost edges—they're already bordered)
        for ci in range(1, cols_per_quad):
            _thick_vline(xs[ci], qy1, qy2, thickness)

        # horizontal grid walls
        for ri in range(1, rows_per_quad):
            _thick_hline(qx1, qx2, ys[ri], thickness)

        # interiors for spawning (tile coords)
        cells = _cell_interiors_from_grid(qx1, qy1, qx2, qy2, rows_per_quad, cols_per_quad, thickness)

        # add concentric rings in each cell (no doors)
        if rings > 0:
            for (cx1, cy1, cx2, cy2) in cells:
                # rings grow inward with step ring_step
                for r in range(1, rings + 1):
                    pad = r * ring_step
                    if cx2 - cx1 > pad*2 + 1 and cy2 - cy1 > pad*2 + 1:
                        wall_box(cx1 + pad, cy1 + pad, cx2 - pad, cy2 - pad)

        all_cells.extend(cells)

    return all_cells

def inner_zones_from_cells(cells, rings: int, ring_step: int = 2, inset: int = 1):
    """
    From the cell interiors returned by wall_quad_concentric, compute the
    innermost open area (inside the deepest ring) for each cell.

    Returns: list of tile-rects (x1, y1, x2, y2) in TILE COORDS (inclusive).
    """
    zones = []
    pad = max(0, rings * max(1, ring_step)) + max(0, inset)  # +inset to avoid ring tiles
    for cx1, cy1, cx2, cy2 in cells:
        zx1 = cx1 + pad
        zy1 = cy1 + pad
        zx2 = cx2 - pad
        zy2 = cy2 - pad
        if zx2 > zx1 and zy2 > zy1:
            zones.append((zx1, zy1, zx2, zy2))
    return zones


def group_zones_by_quadrant(zones):
    """
    Group tile-rects by quadrant index:
      0 = top-left, 1 = top-right, 2 = bottom-left, 3 = bottom-right
    """
    assert walls is not None and len(walls) and len(walls[0]), "utils.walls must be initialized"
    H, W = len(walls), len(walls[0])
    midx, midy = W // 2, H // 2

    quads = [[], [], [], []]
    for (x1, y1, x2, y2) in zones:
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        if cy <= midy:
            qi = 0 if cx <= midx else 1
        else:
            qi = 2 if cx <= midx else 3
        quads[qi].append((x1, y1, x2, y2))
    return quads
