"""Définition des objets principaux du jeu."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple

import pygame
from pygame import Rect

from settings import (
    AIR_ROTATION_SPEED,
    COYOTE_FRAMES,
    GRAVITY,
    GROUND_COLOR,
    GROUND_HIGHLIGHT,
    JUMP_FORCE,
    MAX_FALL_SPEED,
    PLAYER_BORDER_COLOR,
    PLAYER_COLOR,
    PLAYER_SIZE,
    SHADOW_COLOR,
    SPIKE_COLOR,
    SPIKE_SIZE,
)


@dataclass
class GroundSection:
    """Plateforme rectangulaire sur laquelle le joueur peut courir."""

    rect: Rect
    color: Tuple[int, int, int] = GROUND_COLOR
    highlight: Tuple[int, int, int] = GROUND_HIGHLIGHT

    def draw(self, surface: pygame.Surface, cam_x: float) -> None:
        dest = self.rect.move(-cam_x, 0)
        pygame.draw.rect(surface, self.color, dest)
        highlight_rect = pygame.Rect(dest.x, dest.y, dest.width, 6)
        pygame.draw.rect(surface, self.highlight, highlight_rect)


@dataclass
class Spike:
    """Obstacle triangulaire classique de Geometry Dash."""

    x: float
    base_y: float
    size: int = SPIKE_SIZE
    color: Tuple[int, int, int] = SPIKE_COLOR

    @property
    def rect(self) -> Rect:
        return Rect(int(self.x), int(self.base_y - self.size), int(self.size), int(self.size))

    def draw(self, surface: pygame.Surface, cam_x: float) -> None:
        sx = self.x - cam_x
        points = [
            (int(sx), int(self.base_y)),
            (int(sx + self.size / 2), int(self.base_y - self.size)),
            (int(sx + self.size), int(self.base_y)),
        ]
        pygame.draw.polygon(surface, self.color, points)

    def collides(self, player_rect: Rect) -> bool:
        spike_box = self.rect
        if not spike_box.colliderect(player_rect):
            return False
        a = (spike_box.left, spike_box.bottom)
        b = (spike_box.centerx, spike_box.top)
        c = (spike_box.right, spike_box.bottom)
        test_points = [
            (player_rect.left, player_rect.bottom),
            (player_rect.right, player_rect.bottom),
            (player_rect.centerx, player_rect.centery),
        ]
        return any(_point_in_triangle(p, a, b, c) for p in test_points)


def _point_in_triangle(p: Tuple[int, int], a, b, c) -> bool:
    (px, py) = p
    (ax, ay) = a
    (bx, by) = b
    (cx, cy) = c
    denom = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
    if denom == 0:
        return False
    u = ((by - cy) * (px - cx) + (cx - bx) * (py - cy)) / denom
    v = ((cy - ay) * (px - cx) + (ax - cx) * (py - cy)) / denom
    w = 1 - u - v
    return 0 <= u <= 1 and 0 <= v <= 1 and 0 <= w <= 1


class Player:
    """Cube du joueur, avec gestion de la physique et du rendu."""

    def __init__(self, spawn: Tuple[float, float]):
        self.spawn_point = (float(spawn[0]), float(spawn[1]))
        self.rect = pygame.Rect(int(spawn[0]), int(spawn[1]), PLAYER_SIZE, PLAYER_SIZE)
        self._pos_x = float(self.rect.x)
        self._pos_y = float(self.rect.y)
        self.prev_top = self.rect.top
        self.prev_bottom = self.rect.bottom
        self.vel_y = 0.0
        self.on_ground = True
        self.coyote_frames = COYOTE_FRAMES
        self.rotation = 0.0
        self._base_surface = self._create_base_surface()
        self._shadow_surface = self._create_shadow_surface()
        self.reset(spawn)

    def _create_base_surface(self) -> pygame.Surface:
        surf = pygame.Surface((PLAYER_SIZE, PLAYER_SIZE), pygame.SRCALPHA)
        pygame.draw.rect(surf, PLAYER_BORDER_COLOR, (0, 0, PLAYER_SIZE, PLAYER_SIZE), border_radius=10)
        pygame.draw.rect(surf, PLAYER_COLOR, (4, 4, PLAYER_SIZE - 8, PLAYER_SIZE - 8), border_radius=8)
        pygame.draw.circle(surf, (255, 255, 255, 90), (PLAYER_SIZE - 10, 10), 6)
        return surf

    def _create_shadow_surface(self) -> pygame.Surface:
        width = PLAYER_SIZE + 14
        height = max(6, PLAYER_SIZE // 3)
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, SHADOW_COLOR, surf.get_rect())
        return surf

    def reset(self, spawn: Tuple[float, float] | None = None) -> None:
        if spawn is not None:
            self.spawn_point = (float(spawn[0]), float(spawn[1]))
        x, y = self.spawn_point
        self.rect.update(int(x), int(y), PLAYER_SIZE, PLAYER_SIZE)
        self._pos_x = float(self.rect.x)
        self._pos_y = float(self.rect.y)
        self.prev_top = self.rect.top
        self.prev_bottom = self.rect.bottom
        self.vel_y = 0.0
        self.on_ground = True
        self.coyote_frames = COYOTE_FRAMES
        self.rotation = 0.0

    def advance(self, dx: float) -> None:
        self._pos_x += dx
        self.rect.x = int(round(self._pos_x))

    def apply_gravity(self, scale: float = 1.0) -> None:
        self.prev_top = self.rect.top
        self.prev_bottom = self.rect.bottom
        self.vel_y = min(self.vel_y + GRAVITY * scale, MAX_FALL_SPEED)
        self._pos_y += self.vel_y * scale
        self.rect.y = int(round(self._pos_y))

    def handle_ground(self, sections: Iterable[GroundSection]) -> None:
        landed = False
        for section in sections:
            tile = section.rect
            if not self.rect.colliderect(tile):
                continue
            if self.vel_y >= 0 and self.prev_bottom <= tile.top:
                self.rect.bottom = tile.top
                self._pos_y = float(self.rect.y)
                self.vel_y = 0.0
                self.on_ground = True
                self.coyote_frames = COYOTE_FRAMES
                landed = True
                break
            if self.vel_y < 0 and self.prev_top >= tile.bottom:
                self.rect.top = tile.bottom
                self._pos_y = float(self.rect.y)
                self.vel_y = 0.0
                break
        if not landed:
            if self.coyote_frames > 0:
                self.coyote_frames -= 1
            else:
                self.on_ground = False

    def can_jump(self) -> bool:
        return self.on_ground or self.coyote_frames > 0

    def jump(self) -> None:
        self.vel_y = JUMP_FORCE
        self.on_ground = False
        self.coyote_frames = 0
        self._pos_y = float(self.rect.y)

    def update_rotation(self) -> None:
        if self.on_ground:
            self.rotation = 0.0
        else:
            self.rotation = (self.rotation + AIR_ROTATION_SPEED) % 360

    def draw(self, surface: pygame.Surface, cam_x: float) -> None:
        shadow_pos = (
            int(self.rect.centerx - cam_x - self._shadow_surface.get_width() / 2),
            int(self.rect.bottom + 6 - self._shadow_surface.get_height() / 2),
        )
        surface.blit(self._shadow_surface, shadow_pos)
        rotated = pygame.transform.rotate(self._base_surface, self.rotation)
        dest = rotated.get_rect(center=(int(self.rect.centerx - cam_x), int(self.rect.centery)))
        surface.blit(rotated, dest)

    def hits_spikes(self, spikes: Iterable[Spike]) -> bool:
        return any(spike.collides(self.rect) for spike in spikes)
