
import pygame

# Window
WIDTH, HEIGHT = 960, 540
FPS = 60

# World
GRAVITY = 0.9
JUMP_VELOCITY = -17
SPEED = 7.0            # Level scroll speed (px/frame)

# Colors
WHITE = (240, 240, 240)
BLACK = (10, 10, 10)
BG1 = (18, 18, 28)
BG2 = (26, 26, 40)
GROUND_COLOR = (70, 90, 110)
SPIKE_COLOR = (230, 80, 80)
PAD_COLOR = (240, 210, 70)   # jump pad
ORB_COLOR = (80, 200, 255)   # jump orb (press jump while inside)

# Player
PLAYER_SIZE = 36
PLAYER_COLOR = (190, 255, 200)

# Level
GROUND_HEIGHT = 100
TILE = 48

# UI
TITLE = "Mini Geometry Dash (Pygame)"
FONT_NAME = "freesansbold.ttf"
