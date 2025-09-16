
from __future__ import annotations
import pygame
from pygame import Rect
from dataclasses import dataclass
from typing import List, Tuple
from settings import *

@dataclass
class Spike:
    x: float
    base_y: float
    size: int = TILE
    color: Tuple[int,int,int] = SPIKE_COLOR

    @property
    def rect(self) -> Rect:
        return Rect(int(self.x), int(self.base_y - self.size), self.size, self.size)

    def draw(self, surf: pygame.Surface, cam_x: float):
        x = int(self.x - cam_x)
        y = int(self.base_y)
        points = [(x, y), (x + self.size//2, y - self.size), (x + self.size, y)]
        pygame.draw.polygon(surf, self.color, points)

    def collide(self, player_rect: Rect) -> bool:
        # Conservative collision: if player's rect intersects the bounding rect,
        # do a simple half-plane test for the triangle.
        r = self.rect
        if not r.colliderect(player_rect):
            return False
        # Triangle points (A,B,C) with B apex
        A = (r.left, r.bottom)
        B = (r.centerx, r.top)
        C = (r.right, r.bottom)
        # We'll test player's bottom vertices; if either is above triangle edge lines, it's a hit.
        px_left = (player_rect.left, player_rect.bottom)
        px_right = (player_rect.right, player_rect.bottom)
        return self.point_in_triangle(px_left, A,B,C) or self.point_in_triangle(px_right, A,B,C) or r.colliderect(player_rect)

    @staticmethod
    def point_in_triangle(p, a,b,c):
        # Barycentric technique
        (x, y) = p
        (x1,y1) = a; (x2,y2) = b; (x3,y3) = c
        denom = (y2 - y3)*(x1 - x3) + (x3 - x2)*(y1 - y3)
        if denom == 0:
            return False
        w1 = ((y2 - y3)*(x - x3) + (x3 - x2)*(y - y3)) / denom
        w2 = ((y3 - y1)*(x - x3) + (x1 - x3)*(y - y3)) / denom
        w3 = 1 - w1 - w2
        return (0 <= w1 <= 1) and (0 <= w2 <= 1) and (0 <= w3 <= 1)

@dataclass
class JumpPad:
    x: float
    y: float
    w: int = TILE
    h: int = TILE//4
    boost: float = -24.0
    color: Tuple[int,int,int] = PAD_COLOR

    @property
    def rect(self) -> Rect:
        return Rect(int(self.x), int(self.y - self.h), self.w, self.h)

    def draw(self, surf: pygame.Surface, cam_x: float):
        r = self.rect.move(-cam_x, 0)
        pygame.draw.rect(surf, self.color, r, border_radius=6)

    def try_activate(self, player_rect: Rect, vel_y: float) -> Tuple[bool, float]:
        if self.rect.colliderect(player_rect):
            return True, self.boost
        return False, vel_y

@dataclass
class JumpOrb:
    x: float
    y: float
    radius: int = TILE//3
    boost: float = -21.0
    color: Tuple[int,int,int] = ORB_COLOR

    @property
    def rect(self) -> Rect:
        return Rect(int(self.x - self.radius), int(self.y - self.radius), self.radius*2, self.radius*2)

    def draw(self, surf: pygame.Surface, cam_x: float):
        pygame.draw.circle(surf, self.color, (int(self.x - cam_x), int(self.y)), self.radius, 3)

    def inside(self, player_rect: Rect) -> bool:
        return self.rect.colliderect(player_rect)

class Ground:
    def __init__(self, segments: List[pygame.Rect]):
        self.segments = segments

    def draw(self, surf: pygame.Surface, cam_x: float):
        for seg in self.segments:
            pygame.draw.rect(surf, GROUND_COLOR, seg.move(-cam_x, 0))

    def collide(self, rect: Rect) -> pygame.Rect | None:
        for seg in self.segments:
            if seg.colliderect(rect):
                return seg
        return None

class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, PLAYER_SIZE, PLAYER_SIZE)
        self._pos_x = float(self.rect.x)
        self.vel_y = 0
        self.on_ground = False
        self.rotation = 0.0  # for fun

    def advance(self, dx: float):
        """Move the player forward while keeping float precision."""
        self._pos_x += dx
        self.rect.x = int(round(self._pos_x))

    def update(self, ground: Ground, spikes: List[Spike]):
        # Apply gravity
        self.vel_y += GRAVITY
        self.rect.y += int(self.vel_y)

        # Ground collision
        hit = ground.collide(self.rect)
        if hit:
            if self.vel_y >= 0:
                self.rect.bottom = hit.top
                self.vel_y = 0
                self.on_ground = True
            else:
                self.rect.top = hit.bottom
                self.vel_y = 0
                self.on_ground = False
        else:
            self.on_ground = False

        # Rotate while airborne for style
        if not self.on_ground:
            self.rotation = (self.rotation + 8) % 360
        else:
            self.rotation = 0

        # Spike collision
        for s in spikes:
            if s.collide(self.rect):
                return True  # dead
        return False

    def jump(self, strength: float = JUMP_VELOCITY):
        # Can always jump if grounded; otherwise small coyote time feel
        if self.on_ground or self.vel_y > -2:
            self.vel_y = strength

    def draw(self, surf: pygame.Surface, cam_x: float):
        # Draw as a rotated square
        center = (int(self.rect.centerx - cam_x), int(self.rect.centery))
        size = self.rect.width
        # Create a small surface to rotate
        s = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.rect(s, PLAYER_COLOR, (0, 0, size, size), border_radius=6)
        rs = pygame.transform.rotate(s, self.rotation)
        r = rs.get_rect(center=center)
        surf.blit(rs, r.topleft)
