"""Construction du niveau et fonctions utilitaires pour le décor."""

from __future__ import annotations

from typing import Iterable, List, Tuple

import pygame

from objects import GroundSection, Spike
from settings import (
    BACKGROUND_COLUMN_SPACING,
    FINISH_COLOR,
    FINISH_FLAG_HEIGHT,
    GROUND_COLOR,
    GROUND_HEIGHT,
    HEIGHT,
    LEVEL_END_OFFSET,
    PLAYER_SIZE,
    SPIKE_SIZE,
    WIDTH,
)


class Level:
    """Contient la géométrie d'un niveau et les obstacles à éviter."""

    def __init__(self) -> None:
        self.sections: List[GroundSection] = []
        self.spikes: List[Spike] = []
        self.background_columns: List[Tuple[float, int]] = []
        self.player_spawn: Tuple[float, float] = (0.0, 0.0)
        self.finish_x: float = 0.0
        self.length: float = 1.0
        self._build()

    def _build(self) -> None:
        base_y = HEIGHT - GROUND_HEIGHT
        layout = [
            (520, 120),
            (340, 110),
            (360, 140),
            (520, 0),
        ]
        x = 0
        for width, gap in layout:
            rect = pygame.Rect(int(round(x)), base_y, int(width), GROUND_HEIGHT)
            self.sections.append(GroundSection(rect, color=GROUND_COLOR))
            x += width + gap

        if not self.sections:
            raise RuntimeError("Le niveau doit contenir au moins une section de sol.")

        first_section = self.sections[0]
        self.player_spawn = (
            first_section.rect.left + 80,
            first_section.rect.top - PLAYER_SIZE,
        )

        self.spikes = [
            Spike(300, base_y, size=SPIKE_SIZE),
            Spike(720, base_y, size=SPIKE_SIZE),
            Spike(1320, base_y, size=SPIKE_SIZE),
            Spike(1860, base_y, size=SPIKE_SIZE),
        ]

        max_right = max(section.rect.right for section in self.sections)
        self.finish_x = max_right + LEVEL_END_OFFSET
        self.length = max(1.0, self.finish_x - self.player_spawn[0])

        self._build_background_columns()

    def _build_background_columns(self) -> None:
        self.background_columns.clear()
        spacing = BACKGROUND_COLUMN_SPACING
        x = -WIDTH
        index = 0
        while x < self.finish_x + WIDTH:
            height = 80 + (index % 5) * 24
            self.background_columns.append((x, height))
            x += spacing
            index += 1

    def reset(self) -> None:
        """Le niveau est statique, mais l'API reste cohérente."""

    def ground_iter(self) -> Iterable[GroundSection]:
        return self.sections

    def draw(self, surface: pygame.Surface, cam_x: float) -> None:
        for section in self.sections:
            section.draw(surface, cam_x)
        for spike in self.spikes:
            spike.draw(surface, cam_x)
        self._draw_finish(surface, cam_x)

    def _draw_finish(self, surface: pygame.Surface, cam_x: float) -> None:
        pole_x = int(self.finish_x - cam_x)
        pole_top = HEIGHT - GROUND_HEIGHT - FINISH_FLAG_HEIGHT
        pole_rect = pygame.Rect(pole_x, pole_top, 8, FINISH_FLAG_HEIGHT)
        pygame.draw.rect(surface, FINISH_COLOR, pole_rect, border_radius=3)
        base_rect = pygame.Rect(pole_rect.x - 6, pole_rect.bottom - 6, 20, 12)
        pygame.draw.rect(surface, FINISH_COLOR, base_rect, border_radius=4)
        flag_points = [
            (pole_rect.right, pole_rect.top + 18),
            (pole_rect.right + 52, pole_rect.top + 6),
            (pole_rect.right + 52, pole_rect.top + 36),
        ]
        pygame.draw.polygon(surface, FINISH_COLOR, flag_points)

    def hits_spike(self, player_rect: pygame.Rect) -> bool:
        return any(spike.collides(player_rect) for spike in self.spikes)

    def progress(self, x: float) -> float:
        ratio = (x - self.player_spawn[0]) / self.length
        return max(0.0, min(1.0, ratio))
