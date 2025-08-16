import pygame
import random
import rules
import math

class Particle():
    screen_width = 0
    screen_height = 0
    tile_size = 0
    walls = None
    bounce_sound = None

    def __init__(self, pos, direction=None, speed=0, radius = 1, color=None):
        self.pos = pygame.Vector2(pos)

        if color == None:
            self.color = 'black'
        else:
            self.color = color

        # pick a random direction if not specified
        self.velocity = direction * speed if direction is not None else pygame.Vector2(1, 0).rotate(random.uniform(0, 360)) * speed
        self.radius = radius
        self.alive = True
        self.mass = math.pi * self.radius * self.radius

    def screen_collision(self):
        if self.pos.x + self.radius > Particle.screen_width:
            self.pos.x = Particle.screen_width - self.radius
            self.velocity.x *= -rules.BOUNCE
            Particle.bounce_sound.play()
        elif self.pos.x - self.radius < 0:
            self.pos.x = self.radius
            self.velocity.x *= -rules.BOUNCE
            Particle.bounce_sound.play()
        if self.pos.y + self.radius > Particle.screen_height:
            self.pos.y = Particle.screen_height - self.radius
            self.velocity.y *= -rules.BOUNCE
            Particle.bounce_sound.play()
        elif self.pos.y - self.radius < 0:
            self.pos.y = self.radius
            self.velocity.y *= -rules.BOUNCE
            Particle.bounce_sound.play()

    def wall_collision(self):
        ts = Particle.tile_size
        rows = len(Particle.walls)
        cols = len(Particle.walls[0])
        left = max(0, int((self.pos.x-self.radius) // ts))
        right = min(cols-1, int((self.pos.x+self.radius) // ts))
        top  = max(0, int((self.pos.y-self.radius) // ts))
        bottom = min(rows-1, int((self.pos.y+self.radius) // ts))
        for ty in range(top, bottom+1):
            for tx in range(left, right+1):
                if Particle.walls[ty][tx] <= 0: continue
                rect = tile_rect(tx,ty)
                cx = max(rect.left,  min(self.pos.x, rect.right))
                cy = max(rect.top,   min(self.pos.y, rect.bottom))
                dx, dy = self.pos.x - cx, self.pos.y - cy
                if dx*dx + dy*dy >= self.radius*self.radius: continue
                self.change_mass(10)                     # bite
                pen_x = self.radius - abs(dx)
                pen_y = self.radius - abs(dy)
                if pen_y < pen_x:
                    self.velocity.y *= -1
                    self.pos.y += math.copysign(pen_y, dy)
                else:
                    self.velocity.x *= -1
                    self.pos.x += math.copysign(pen_x, dx)
                Particle.walls[ty][tx] -= 1

    def change_mass(self, dm):
        old = self.mass
        self.mass = max(0, self.mass + dm) # don't go below 0
        self.radius = math.sqrt(self.mass / math.pi)

        # if self.mass > 0: # avoid / 0
            # self.velocity *= math.sqrt(old / self.mass) # keep kinetic energy

        return self.mass - old # return actual change

    def update(self, dt):
        if self.mass <= 0:
            self.alive = False
            return
        self.velocity.y += rules.GRAVITY * dt
        self.pos += self.velocity * dt
        self.wall_collision()
        self.screen_collision()

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, self.pos, self.radius)

    def get_potential_energy(self):
        return self.mass * rules.GRAVITY * (Particle.screen_height - self.pos.y )
    
    def get_kinetic_energy(self):
        return 0.5 * self.mass * self.velocity.length_squared()
    
    def get_total_energy(self):
        return self.get_kinetic_energy() + self.get_potential_energy()
    
def tile_rect(tx, ty):
        ts = Particle.tile_size
        return pygame.Rect(tx*ts, ty*ts, ts, ts)
    