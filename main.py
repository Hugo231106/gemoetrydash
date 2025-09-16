
import pygame, sys
from settings import *
from level import Level
from objects import Player

STATE_MENU = 0
STATE_PLAY = 1
STATE_DEAD = 2
STATE_WIN = 3

def draw_bg(screen, cam_x):
    # Parallax background
    screen.fill(BG1)
    # Simple moving stripes
    for i in range(0, WIDTH, 80):
        x = (i - int(cam_x*0.2)) % WIDTH
        pygame.draw.rect(screen, BG2, (x, 0, 40, HEIGHT))

def text(screen, s, size, x, y, center=True, color=WHITE):
    f = pygame.font.Font(FONT_NAME, size)
    img = f.render(s, True, color)
    r = img.get_rect()
    if center:
        r.center = (x, y)
    else:
        r.topleft = (x, y)
    screen.blit(img, r)

def run():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    state = STATE_MENU
    level = Level()
    player = Player(120, HEIGHT - GROUND_HEIGHT - PLAYER_SIZE)
    cam_x = 0.0
    speed = SPEED
    jump_buffer = 0  # frames

    while True:
        dt = clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                if state == STATE_MENU and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    state = STATE_PLAY
                elif state in (STATE_DEAD, STATE_WIN) and event.key in (pygame.K_r, pygame.K_SPACE, pygame.K_RETURN):
                    # reset
                    level = Level()
                    player = Player(120, HEIGHT - GROUND_HEIGHT - PLAYER_SIZE)
                    cam_x = 0.0
                    jump_buffer = 0
                    state = STATE_PLAY
                elif state == STATE_PLAY and event.key == pygame.K_SPACE:
                    jump_buffer = 6  # allow a small window to jump

        keys = pygame.key.get_pressed()
        if state == STATE_PLAY:
            # Auto-runner: advance the player and camera together
            player.advance(speed)
            cam_x += speed

            # Input: jump
            jump_pressed = False
            if jump_buffer > 0:
                jump_pressed = True
                jump_buffer -= 1

            # Interactives (pads/orbs)
            player.vel_y = level.try_activate_interactives(player.rect, player.vel_y, jump_pressed or keys[pygame.K_SPACE])

            if jump_pressed or (keys[pygame.K_SPACE] and player.on_ground):
                player.jump()

            # Update physics and collisions
            dead = player.update(level.ground, level.spikes)
            if dead:
                state = STATE_DEAD

            # Win condition
            if player.rect.centerx >= level.finish_x:
                state = STATE_WIN

        # Drawing
        draw_bg(screen, cam_x)
        if state == STATE_MENU:
            text(screen, TITLE, 36, WIDTH//2, HEIGHT//2 - 60)
            text(screen, "Espace/Entrée : Jouer", 24, WIDTH//2, HEIGHT//2 + 10)
            text(screen, "Échap : Quitter", 20, WIDTH//2, HEIGHT//2 + 50)
        else:
            level.draw(screen, cam_x)
            # Shadow for player
            pygame.draw.rect(screen, (0,0,0,40), (player.rect.x-4 - cam_x, player.rect.y+6, player.rect.w+8, player.rect.h+8), border_radius=8)
            player.draw(screen, cam_x)

        if state == STATE_DEAD:
            text(screen, "💥 Ouch ! Appuie sur R ou Espace pour recommencer", 22, WIDTH//2, HEIGHT//2)
        if state == STATE_WIN:
            text(screen, "🏁 GG ! Niveau terminé — R ou Espace pour rejouer", 22, WIDTH//2, HEIGHT//2)

        # HUD
        if state in (STATE_PLAY, STATE_DEAD, STATE_WIN):
            text(screen, "Espace: Saut  |  R: Rejouer  |  Échap: Quitter", 16, WIDTH//2, 20)

        pygame.display.flip()

if __name__ == "__main__":
    run()
