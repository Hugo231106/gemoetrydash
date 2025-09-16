
from __future__ import annotations
import pygame
from typing import List, Tuple
from settings import *
from objects import Ground, Spike, JumpPad, JumpOrb

class Level:
    def __init__(self):
        self.ground = self._build_ground()
        self.spikes: List[Spike] = []
        self.pads: List[JumpPad] = []
        self.orbs: List[JumpOrb] = []
        self.finish_x = 0

        self._build_course()

    def _build_ground(self) -> Ground:
        base_y = HEIGHT - GROUND_HEIGHT
        segments = []
        # Start platform
        segments.append(pygame.Rect(0, base_y, 1200, GROUND_HEIGHT))
        # Series of platforms with gaps
        x = 1200
        for w, gap in [(500, 200), (400, 160), (700, 240), (600, 180), (900, 260)]:
            segments.append(pygame.Rect(x, base_y, w, GROUND_HEIGHT))
            x += w + gap
        # Long final stretch
        segments.append(pygame.Rect(x, base_y, 1200, GROUND_HEIGHT))
        self.finish_x = x + 1100
        return Ground(segments)

    def _build_course(self):
        base_y = HEIGHT - GROUND_HEIGHT
        # Place spikes clusters
        def add_spike_cluster(start_x, count, spacing=TILE):
            for i in range(count):
                self.spikes.append(Spike(start_x + i*spacing, base_y))

        add_spike_cluster(700, 3)
        add_spike_cluster(1500, 4)
        add_spike_cluster(2350, 2)
        add_spike_cluster(3200, 5, spacing=TILE//1.2)

        # Pads
        self.pads += [
            JumpPad(1150, base_y, boost=-23),
            JumpPad(2050, base_y, boost=-25),
            JumpPad(2700, base_y, boost=-24),
            JumpPad(3750, base_y, boost=-26),
        ]

        # Orbs (need to press jump while inside)
        self.orbs += [
            JumpOrb(1680, base_y-100, boost=-18),
            JumpOrb(2460, base_y-120, boost=-18),
            JumpOrb(4100, base_y-110, boost=-18),
        ]

    def draw(self, surf: pygame.Surface, cam_x: float):
        self.ground.draw(surf, cam_x)
        for s in self.spikes:
            s.draw(surf, cam_x)
        for p in self.pads:
            p.draw(surf, cam_x)
        for o in self.orbs:
            o.draw(surf, cam_x)

    def try_activate_interactives(self, player_rect, player_vel_y, jump_pressed):
        # Pads auto-activate
        for p in self.pads:
            hit, vy = p.try_activate(player_rect, player_vel_y)
            if hit:
                player_vel_y = vy
        # Orbs require jump pressed and overlap
        if jump_pressed:
            for o in self.orbs:
                if o.inside(player_rect):
                    player_vel_y = o.boost
        return player_vel_y
