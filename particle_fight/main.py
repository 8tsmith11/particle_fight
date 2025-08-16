from os.path import join
import pygame
from particle import Particle
from random import randint
import random
from rules import does_eat
import rules
import utils
import theme


# setup
pygame.init()

SCREEN_WIDTH, SCREEN_HEIGHT = 1080, 1920
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), display=1)

TILE_SIZE = 20 # size of wall tile in pixels
SUBSTEPS = 40
utils.tile_size = TILE_SIZE
GRID_WIDTH, GRID_HEIGHT = SCREEN_WIDTH // TILE_SIZE, SCREEN_HEIGHT // TILE_SIZE # size of world in wall tiles

clock = pygame.time.Clock()

font = pygame.font.SysFont(None, 36)
clack_sound = pygame.mixer.Sound(join('audio', 'clack.wav'))
clack_sound.set_volume(0.1)
Particle.bounce_sound = clack_sound

# functions

# elastic collision between two particles
from pygame.math import Vector2
EPS = 1e-6

def elastic_collision(p1, p2, e=1.0):
    disp = p1.pos - p2.pos
    dist = disp.length()

    # skip if not collided or dist is 0 (kept from your original)
    if dist > p1.radius + p2.radius or dist == 0:
        return

    if p1.color != p2.color:
        if p1.mass > p2.mass:
            p1.change_mass(-p2.change_mass(-p2.mass))
            return
        elif p2.mass > p1.mass:
            p2.change_mass(-p1.change_mass(-p1.mass))
            return
        
    clack_sound.play()

    # masses -> inverse masses (supports very heavy/immovable with inf)
    inv1 = 0.0 if p1.mass == float('inf') else 1.0 / p1.mass
    inv2 = 0.0 if p2.mass == float('inf') else 1.0 / p2.mass
    denom = inv1 + inv2
    if denom == 0.0:
        return

    # seperate if overlapping (mass-weighted)
    overlap = p1.radius + p2.radius - dist
    direction = disp.normalize()
    correction = direction * (overlap / denom)
    p1.pos += correction * inv1
    p2.pos -= correction * inv2

    # bounce (impulse with mass + restitution)
    normal = (p1.pos - p2.pos).normalize()
    rel_vel = p1.velocity - p2.velocity
    vn = rel_vel.dot(normal)
    if vn >= 0:
        return
    j = -(1.0 + e) * vn / denom
    impulse = normal * j
    p1.velocity += impulse * inv1
    p2.velocity -= impulse * inv2

# create grid background
grid_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
grid_surface.fill('white')
for x in range(0, SCREEN_WIDTH, TILE_SIZE):
    pygame.draw.line(grid_surface, 'lightgray', (x, 0), (x, SCREEN_HEIGHT))
for y in range(0, SCREEN_HEIGHT, TILE_SIZE):
    pygame.draw.line(grid_surface, 'lightgray', (0, y), (SCREEN_WIDTH, y))


# initialize particles
Particle.screen_width = SCREEN_WIDTH
Particle.screen_height = SCREEN_HEIGHT
particles = []
utils.particles = particles

# initialize walls
walls = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
Particle.tile_size = TILE_SIZE
Particle.walls = walls
utils.walls = walls
 
# Build world
#utils.wall_box(0, 0, GRID_WIDTH - 1, GRID_HEIGHT - 1)
cells = utils.wall_quad_concentric(2, 2, thickness=3, rings=0, ring_step = 2, reset = True)
zones = cells
quad_zones = utils.group_zones_by_quadrant(zones)
quad_colors = theme.NEON["species"][:4]
for qi, rects in enumerate(quad_zones):
    color = quad_colors[qi % len(quad_colors)]
    for (tx1, ty1, tx2, ty2) in rects:
        # convert TILE → PIXEL (inclusive rect)
        x1p, y1p = tx1 * utils.tile_size,      ty1 * utils.tile_size 
        x2p, y2p = (tx2 + 1) * utils.tile_size, (ty2 + 1) * utils.tile_size
        start = len(particles)
        utils.spawn_particles_pixels(x1p, y1p, x2p, y2p, count=2, radius=10, speed=200)
        # set color for this quadrant
        for p in particles[start:]:
            p.color = color

# main loop
running = True
while running:
    dt = clock.tick() / 1000

    # event loop
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    sub_dt = dt / SUBSTEPS
    for _ in range(SUBSTEPS):
        for p in particles:
            p.update(sub_dt)

    particles = [p for p in particles if p.alive] # remove dead particles

    for i in range(len(particles)):
        for j in range(i + 1, len(particles)):
            elastic_collision(particles[i], particles[j])

    # draw background
    #screen.blit(grid_surface, (0,0))
    screen.fill(theme.NEON["bg"])

    # draw particles
    for p in particles:
        p.draw(screen)

    # Draw energy levels
    # energy_text = font.render("Total Energy: " + str(utils.sum_total_energy(particles)), True, 'black')
    # text_rect = energy_text.get_rect(topleft = (0,0))
    # screen.blit(energy_text, text_rect)

    # draw walls
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            if walls[y][x] > 0:
                rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(screen, theme.wall_color(walls[y][x], rules.WALL_HEALTH), rect)
                pygame.draw.rect(screen, (20, 22, 30), rect, width=2)

                # draw health 
                #health_text = font.render(str(walls[y][x]), True, (255, 255, 255))
                #text_rect = health_text.get_rect(center=rect.center)
                #screen.blit(health_text, text_rect)

    utils.particles = particles
    
    pygame.display.update()

pygame.quit()