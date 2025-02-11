import pygame

pygame.init()
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
GRID_SIZE = 8
CELL_SIZE = 50
icon_image = pygame.image.load("icon.jpg")
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
sound_on = True
dark_theme = False
DB_NAME = 'data/Save.sqlite'

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 123, 255)
RED = (255, 0, 0)
ORANGE = (255, 165, 0)
GREEN = (0, 200, 150)
DARK_BLUE = (10, 10, 80)
LIGHT_BLUE = (173, 216, 230)
GRAY = (200, 200, 200)
DARK_GRAY = (80, 80, 70)
PURPLE = (95, 70, 120)
YELLOW = (255, 255, 0)

font_large = pygame.font.Font(None, 100)
font_medium = pygame.font.Font(None, 50)
font_small = pygame.font.Font(None, 30)

cursor_image = pygame.image.load("data/cursor.png")
cursor_image = pygame.transform.scale(cursor_image, (32, 32))
clock_icon = pygame.image.load("data/clock_icon.png")
clock_icon = pygame.transform.scale(clock_icon, (40, 40))
infinity_icon = pygame.image.load("data/infinity_icon.png")
infinity_icon = pygame.transform.scale(infinity_icon, (75, 60))
settings_icon = pygame.image.load("data/settings-icon.png")
settings_icon = pygame.transform.scale(settings_icon, (50, 50))
crown_image = pygame.image.load("data/crown.png")
crown_image = pygame.transform.scale(crown_image, (40, 40))
rules_icon = pygame.image.load("data/rules_icon.png")
rules_icon = pygame.transform.scale(rules_icon, (50, 50))
donate_icon = pygame.image.load("data/donate_icon.png")
donate_icon = pygame.transform.scale(donate_icon, (70, 70))

BLOCK_SPRITES = {
    "blue": pygame.image.load("data/sprites/blue_cube.jpg"),
    "green": pygame.image.load("data/sprites/green_cube.jpg"),
    "red": pygame.image.load("data/sprites/red_cube.jpg"),
    "orange": pygame.image.load("data/sprites/yellow_cube.jpg"),
}

SHAPES = [
    [[1, 1], [1, 1]],  # Квадрат
    [[1, 1, 1]],  # Линия горизонтальная
    [[1, 1, 1]],  # Линия горизонтальная
    [[1, 1, 1]],  # Линия горизонтальная
    [[1], [1], [1]],  # Линия вертикальная
    [[1], [1], [1]],  # Линия вертикальная
    [[1], [1], [1]],  # Линия вертикальная
    [[1, 1, 0], [0, 1, 1]],  # Z-образная
    [[0, 1, 1], [1, 1, 0]],  # Обратная Z-образная
    [[1, 1, 1], [0, 1, 0]],  # T-образная
    [[0, 1, 0], [1, 1, 1]],  # T-образная
    [[1], [1, 1], [1]],  # T-образная
    [[0, 1], [1, 1], [0, 1]],  # T-образная
    [[1, 1, 1], [1, 1, 1], [1, 1, 1]],  # Квадрат 3*3
    [[1, 1, 1], [1, 1, 1]],  # Прямоугольник горизонтальный
    [[1, 1], [1, 1], [1, 1]],  # Прямоугольник вертикальный
    [[1]],  # Везучий квадрат
    [[1], [1, 1, 1]],  # Крюк1
    [[0, 0, 1], [1, 1, 1]],  # Крюк2
    [[1, 1, 1], [1]],  # Крюк3
    [[1, 1, 1], [0, 0, 1]],  # Крюк4
    [[1, 1], [1, 1]],  # Квадрат
    [[1, 1, 1]],  # Линия горизонтальная
    [[1, 1, 1]],  # Линия горизонтальная
    [[1, 1, 1]],  # Линия горизонтальная
    [[1], [1], [1]],  # Линия вертикальная
    [[1], [1], [1]],  # Линия вертикальная
    [[1], [1], [1]],  # Линия вертикальная
    [[1, 1, 0], [0, 1, 1]],  # Z-образная
    [[0, 1, 1], [1, 1, 0]],  # Обратная Z-образная
    [[1, 1, 1], [0, 1, 0]],  # T-образная
    [[0, 1, 0], [1, 1, 1]],  # T-образная
    [[1], [1, 1], [1]],  # T-образная
    [[0, 1], [1, 1], [0, 1]],  # T-образная
    [[1, 1, 1], [1, 1, 1], [1, 1, 1]],  # Квадрат 3*3
    [[1, 1, 1], [1, 1, 1]],  # Прямоугольник горизонтальный
    [[1, 1], [1, 1], [1, 1]],  # Прямоугольник вертикальный
    [[1], [1, 1, 1]],  # Крюк1
    [[0, 0, 1], [1, 1, 1]],  # Крюк2
    [[1, 1, 1], [1]],  # Крюк3
    [[1, 1, 1], [0, 0, 1]], # Крюк4
    [[1], [1], [1, 1, 1]], # 3*3 крюк
    [[0, 0, 1], [0, 0, 1], [1, 1, 1]], # 3*3 крюк
    [[1, 1, 1], [1], [1]], # 3*3 крюк
    [[1, 1, 1], [0, 0, 1], [0, 0, 1]], # 3*3 крюк
    [[1], [1], [1, 1, 1]], # 3*3 крюк
    [[0, 0, 1], [0, 0, 1], [1, 1, 1]], # 3*3 крюк
    [[1, 1, 1], [1], [1]], # 3*3 крюк
    [[1, 1, 1], [0, 0, 1], [0, 0, 1]] # 3*3 крюк
]