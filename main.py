"""Point d'entrée du Geometry Dash simplifié."""

from __future__ import annotations

import sys
from typing import Dict

import pygame

from level import Level
from objects import Player
from settings import (
    BACKGROUND_COLUMN_COLOR,
    BACKGROUND_COLUMN_WIDTH,
    BACKGROUND_GRADIENT_BOTTOM,
    BACKGROUND_GRADIENT_TOP,
    BACKGROUND_STRIPE_COLOR,
    BACKGROUND_STRIPE_SPACING,
    BACKGROUND_STRIPE_WIDTH,
    CAMERA_OFFSET_X,
    FONT_NAME,
    FPS,
    GROUND_HEIGHT,
    HEIGHT,
    HUD_BACKGROUND,
    HUD_COLOR,
    HUD_SHADOW_COLOR,
    JUMP_BUFFER_FRAMES,
    RUN_SPEED,
    TARGET_FRAME_DURATION,
    TITLE,
    WIDTH,
)

STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_DEAD = "dead"
STATE_WIN = "win"


def create_vertical_gradient(size: tuple[int, int], top: tuple[int, int, int], bottom: tuple[int, int, int]) -> pygame.Surface:
    width, height = size
    gradient = pygame.Surface((width, height)).convert()
    for y in range(height):
        ratio = y / max(height - 1, 1)
        color = tuple(int(top[c] + (bottom[c] - top[c]) * ratio) for c in range(3))
        pygame.draw.line(gradient, color, (0, y), (width, y))
    return gradient


def draw_background(surface: pygame.Surface, gradient: pygame.Surface, cam_x: float, level: Level) -> None:
    surface.blit(gradient, (0, 0))
    offset = (cam_x * 0.25) % BACKGROUND_STRIPE_SPACING
    start = -BACKGROUND_STRIPE_SPACING
    end = WIDTH + BACKGROUND_STRIPE_SPACING
    for x in range(start, end, BACKGROUND_STRIPE_SPACING):
        stripe_rect = pygame.Rect(int(x - offset), 0, BACKGROUND_STRIPE_WIDTH, HEIGHT)
        pygame.draw.rect(surface, BACKGROUND_STRIPE_COLOR, stripe_rect)
    for column_x, column_height in level.background_columns:
        screen_x = int(column_x - cam_x * 0.5)
        rect = pygame.Rect(screen_x, HEIGHT - GROUND_HEIGHT - column_height, BACKGROUND_COLUMN_WIDTH, column_height)
        pygame.draw.rect(surface, BACKGROUND_COLUMN_COLOR, rect, border_radius=6)


def draw_centered_text(surface: pygame.Surface, font: pygame.font.Font, text: str, position: tuple[int, int]) -> None:
    img = font.render(text, True, HUD_COLOR)
    rect = img.get_rect(center=position)
    surface.blit(img, rect)


def draw_banner(surface: pygame.Surface, font: pygame.font.Font, text: str) -> None:
    img = font.render(text, True, HUD_COLOR)
    rect = img.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    background = rect.inflate(32, 24)
    shadow = background.inflate(12, 12)
    pygame.draw.rect(surface, HUD_SHADOW_COLOR, shadow, border_radius=16)
    pygame.draw.rect(surface, HUD_BACKGROUND, background, border_radius=16)
    surface.blit(img, rect)


def draw_hud(surface: pygame.Surface, fonts: Dict[str, pygame.font.Font], progress: float, attempt: int, state: str) -> None:
    bar_rect = pygame.Rect(WIDTH // 2 - 160, 24, 320, 16)
    shadow_rect = bar_rect.inflate(8, 8)
    pygame.draw.rect(surface, HUD_SHADOW_COLOR, shadow_rect, border_radius=10)
    pygame.draw.rect(surface, HUD_BACKGROUND, bar_rect, border_radius=8)
    inner_rect = bar_rect.inflate(-4, -4)
    inner_rect.width = int(inner_rect.width * progress)
    if inner_rect.width > 0:
        pygame.draw.rect(surface, HUD_COLOR, inner_rect, border_radius=6)
    percent = fonts["tiny"].render(f"{int(progress * 100):02d}%", True, HUD_COLOR)
    percent_rect = percent.get_rect(midtop=(bar_rect.centerx, bar_rect.bottom + 6))
    surface.blit(percent, percent_rect)

    if attempt > 0 and state != STATE_MENU:
        attempt_img = fonts["small"].render(f"Essai {attempt}", True, HUD_COLOR)
        surface.blit(attempt_img, (20, 20))

    controls_text = "Espace : saut  |  R : recommencer  |  Échap : quitter"
    controls_img = fonts["tiny"].render(controls_text, True, HUD_COLOR)
    controls_rect = controls_img.get_rect(midbottom=(WIDTH // 2, HEIGHT - 16))
    surface.blit(controls_img, controls_rect)


def run() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    gradient = create_vertical_gradient((WIDTH, HEIGHT), BACKGROUND_GRADIENT_TOP, BACKGROUND_GRADIENT_BOTTOM)

    fonts = {
        "title": pygame.font.Font(FONT_NAME, 54),
        "medium": pygame.font.Font(FONT_NAME, 28),
        "small": pygame.font.Font(FONT_NAME, 22),
        "tiny": pygame.font.Font(FONT_NAME, 16),
    }

    level = Level()
    player = Player(level.player_spawn)

    cam_x = 0.0
    state = STATE_MENU
    attempt = 0
    jump_buffer = 0
    jump_held = False

    def start_run(start_with_jump: bool) -> None:
        nonlocal state, attempt, cam_x, jump_buffer, jump_held
        level.reset()
        player.reset(level.player_spawn)
        cam_x = 0.0
        jump_buffer = JUMP_BUFFER_FRAMES if start_with_jump else 0
        jump_held = start_with_jump
        state = STATE_PLAYING
        attempt += 1

    while True:
        dt = clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_SPACE:
                    if state == STATE_PLAYING:
                        jump_buffer = JUMP_BUFFER_FRAMES
                    jump_held = True
                if state == STATE_MENU and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    start_run(event.key == pygame.K_SPACE)
                elif state in (STATE_DEAD, STATE_WIN) and event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_r):
                    start_run(event.key == pygame.K_SPACE)
            if event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
                jump_held = False

        if state == STATE_PLAYING:
            scale = max(0.5, min(2.0, dt / TARGET_FRAME_DURATION))
            player.advance(RUN_SPEED * scale)
            player.apply_gravity(scale)
            player.handle_ground(level.ground_iter())
            if player.can_jump() and (jump_buffer > 0 or jump_held):
                player.jump()
                jump_buffer = 0
            elif jump_buffer > 0:
                jump_buffer -= 1
            player.update_rotation()

            if player.hits_spikes(level.spikes) or player.rect.top > HEIGHT + 200:
                state = STATE_DEAD
                jump_buffer = 0
                jump_held = False
            elif player.rect.left >= level.finish_x:
                state = STATE_WIN
                jump_buffer = 0
                jump_held = False

            target_cam = max(0.0, player.rect.centerx - CAMERA_OFFSET_X)
            cam_x += (target_cam - cam_x) * 0.12
        elif state in (STATE_DEAD, STATE_WIN):
            player.update_rotation()

        if state == STATE_MENU:
            player.reset(level.player_spawn)
            cam_x = 0.0

        progress_value = level.progress(player.rect.centerx if state != STATE_MENU else level.player_spawn[0])
        if state == STATE_WIN:
            progress_value = 1.0

        draw_background(screen, gradient, cam_x, level)
        level.draw(screen, cam_x)
        player.draw(screen, cam_x)

        if state == STATE_MENU:
            draw_centered_text(screen, fonts["title"], "Geometry Dash - Premier saut", (WIDTH // 2, HEIGHT // 2 - 90))
            draw_centered_text(screen, fonts["medium"], "Appuie sur ESPACE pour lancer la course", (WIDTH // 2, HEIGHT // 2))
            draw_centered_text(screen, fonts["small"], "Maintiens ESPACE pour enchaîner les sauts", (WIDTH // 2, HEIGHT // 2 + 40))
        elif state == STATE_DEAD:
            draw_banner(screen, fonts["medium"], "Aïe ! Un pic t'a arrêté…")
        elif state == STATE_WIN:
            draw_banner(screen, fonts["medium"], "Bravo ! Niveau terminé 🎉")

        draw_hud(screen, fonts, progress_value, attempt, state)
        pygame.display.flip()


if __name__ == "__main__":
    run()
