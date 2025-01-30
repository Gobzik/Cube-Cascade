import sqlite3
import pygame
import sys
import random
import time
import os

pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
GRID_SIZE = 8
CELL_SIZE = 50
icon_image = pygame.image.load("data/icon.jpg")
pygame.display.set_icon(icon_image)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Cube Cascade")
sound_on = True
dark_theme = False
pygame.mouse.set_visible(False)
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


def initialize_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Таблица для игрового поля Classic
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS classic_grid (
        id INTEGER PRIMARY KEY,
        x INTEGER,
        y INTEGER,
        value INTEGER
    )
    """)

    # Таблица для игрового поля Adventure
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS adventure_grid (
        id INTEGER PRIMARY KEY,
        x INTEGER,
        y INTEGER,
        value INTEGER
    )
    """)

    # Таблица для текущего счета и рекорда
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scores (
        id INTEGER PRIMARY KEY,
        current_score INTEGER DEFAULT 0,
        high_score INTEGER DEFAULT 0
    )
    """)

    # Таблица для уровней Adventure
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS levels (
        id INTEGER PRIMARY KEY,
        level_number INTEGER,
        required_score INTEGER,
        unlocked INTEGER DEFAULT 0
    )
    """)

    # Таблица для сохранения фигур
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pieces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shape TEXT NOT NULL,
            x INTEGER NOT NULL,
            y INTEGER NOT NULL,
            mode TEXT NOT NULL
        )
        """)

    conn.commit()
    conn.close()


initialize_database()


class Button:
    def __init__(self, text, x, y, width, height, color, hover_color, animation_speed=1, icon=None):
        self.text = text
        self.icon = icon
        self.rect = pygame.Rect(x, y, width, height)
        self.base_rect = self.rect.copy()
        self.color = color
        self.hover_color = hover_color
        self.icon = icon
        self.animation_speed = animation_speed
        self.growth = 1.1

    def draw(self, screen, mouse_pos):
        if self.rect.collidepoint(mouse_pos):
            target_width = self.base_rect.width * self.growth
            target_height = self.base_rect.height * self.growth
            self.rect.width += int((target_width - self.rect.width) * self.animation_speed)
            self.rect.height += int((target_height - self.rect.height) * self.animation_speed)

            self.rect.center = self.base_rect.center
            current_color = self.hover_color
        else:
            self.rect.width += int((self.base_rect.width - self.rect.width) * self.animation_speed)
            self.rect.height += int((self.base_rect.height - self.rect.height) * self.animation_speed)
            self.rect.center = self.base_rect.center
            current_color = self.color

        pygame.draw.rect(screen, current_color, self.rect, border_radius=15)

        if self.icon:
            icon_rect = self.icon.get_rect(midleft=(self.rect.left + 20, self.rect.centery))
            screen.blit(self.icon, icon_rect)

        text_surface = font_medium.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def is_clicked(self, mouse_pos, mouse_pressed):
        return self.rect.collidepoint(mouse_pos) and mouse_pressed


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

buttons = [
    Button("Adventure", SCREEN_WIDTH // 2 - 150, 200, 300, 70, ORANGE, (255, 200, 100), icon=clock_icon, animation_speed=0.5),
    Button("Classic", SCREEN_WIDTH // 2 - 150, 300, 300, 70, GREEN, (100, 255, 200), icon=infinity_icon, animation_speed=0.5),
    Button("Settings", SCREEN_WIDTH // 2 - 150, 500, 300, 70, BLUE, (100, 150, 255), icon=settings_icon, animation_speed=0.5),
    Button("", SCREEN_WIDTH // 2 - 150, 400, 125, 70, PURPLE, (150, 100, 200), icon=rules_icon, animation_speed=0.5),
    Button("", SCREEN_WIDTH // 2 + 25, 400, 125, 70, PURPLE, (150, 100, 200), icon=donate_icon, animation_speed=0.5)
]
back_to_menu_button = Button("Back", SCREEN_WIDTH - 200, 20, 180, 50, ORANGE, (255, 200, 100), animation_speed=0.5)


class Snowflake:
    def __init__(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(-SCREEN_HEIGHT, 0)
        self.size = random.randint(2, 5)
        self.speed = random.randint(10, 30) / FPS

    def fall(self):
        self.y += self.speed
        if self.y > SCREEN_HEIGHT:
            self.y = random.randint(-50, -10)
            self.x = random.randint(0, SCREEN_WIDTH)

    def draw(self, screen):
        pygame.draw.circle(screen, WHITE, (self.x, self.y), self.size)


snowflakes = [Snowflake() for _ in range(150)]


def draw_rainbow_text(text, font, x, y, base_color, screen):
    rainbow_colors = [
        (255, 0, 0),
        (255, 127, 0),
        (255, 255, 0),
        (0, 255, 0),
        (0, 255, 255),
        (0, 0, 255),
        (139, 0, 255)
    ]

    elapsed_time = time.time()
    letter_spacing = 5
    x_offset = x

    for i, char in enumerate(text):
        color_index = int((elapsed_time * 2 + i * letter_spacing) % len(rainbow_colors))
        letter_color = rainbow_colors[color_index]
        letter_surface = font.render(char, True, letter_color)
        screen.blit(letter_surface, (x_offset, y))
        x_offset += letter_surface.get_width()


def draw_gradient_background(screen, top_color, bottom_color):
    for y in range(SCREEN_HEIGHT):
        color = [
            top_color[i] + (bottom_color[i] - top_color[i]) * y // SCREEN_HEIGHT
            for i in range(3)
        ]
        pygame.draw.line(screen, color, (0, y), (SCREEN_WIDTH, y))


class BackgroundCube:
    def __init__(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(0, SCREEN_HEIGHT)
        self.size = random.randint(5, 15)
        self.speed = random.uniform(0.2, 0.7)
        self.color = random.choice([(255, 255, 255), (200, 200, 200), (150, 150, 150)])

    def move(self):
        self.y += self.speed
        if self.y > SCREEN_HEIGHT:
            self.y = -self.size
            self.x = random.randint(0, SCREEN_WIDTH)

    def draw(self, screen):
        surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        surface.fill((*self.color, 50))
        screen.blit(surface, (self.x, self.y))


background_cubes = [BackgroundCube() for _ in range(75)]


class ExplosionParticle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = random.randint(3, 6)
        self.life = 60
        self.speed = [random.uniform(-2, 2), random.uniform(-5, -1)]
        self.color = random.choice([ORANGE, RED, YELLOW])

    def update(self):
        self.x += self.speed[0]
        self.y += self.speed[1]
        self.life -= 5

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size)


class Grid:
    def __init__(self, obstacles=None, mode="classic"):
        self.grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.mode = mode
        if obstacles:
            for x, y in obstacles:
                self.grid[y][x] = 1
        self.load_from_database()
        self.score, self.high_score = self.load_scores()
        self.explosion_particles = []

    def draw(self):
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                color = GRAY if self.grid[row][col] == 0 else BLUE
                rect = pygame.Rect(100 + col * CELL_SIZE, 100 + row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(screen, color, rect)
                pygame.draw.rect(screen, WHITE, rect, 1)

        high_score_text = font_medium.render(f"{self.high_score}", True, RED)
        screen.blit(crown_image, (10, 5))
        screen.blit(high_score_text, (50, 10))

        current_score_text = font_medium.render(f"{self.score}", True, ORANGE)
        text_rect = current_score_text.get_rect(center=(SCREEN_WIDTH // 2 - 100, 85))
        screen.blit(current_score_text, text_rect)

    def can_place(self, shape, x, y):
        for r, row in enumerate(shape):
            for c, cell in enumerate(row):
                if cell:
                    grid_x = x + c
                    grid_y = y + r
                    if grid_x >= GRID_SIZE or grid_y >= GRID_SIZE or grid_x < 0 or grid_y < 0 or self.grid[grid_y][
                        grid_x] != 0:
                        return False
        return True

    def place(self, shape, x, y):
        for r, row in enumerate(shape):
            for c, cell in enumerate(row):
                if cell:
                    self.grid[y + r][x + c] = 1
        self.check_lines()
        self.save_to_database()

    def check_lines(self):
        full_rows = [r for r in range(GRID_SIZE) if all(self.grid[r])]
        full_cols = [c for c in range(GRID_SIZE) if all(self.grid[r][c] for r in range(GRID_SIZE))]

        for r in full_rows:
            for c in range(GRID_SIZE):
                self._add_particles(100 + c * CELL_SIZE, 100 + r * CELL_SIZE)
                self.grid[r][c] = 0
            self.score += 10 * GRID_SIZE
            if sound_on:
                pygame.mixer.Sound("data/line_clear.mp3").play()

        for c in full_cols:
            for r in range(GRID_SIZE):
                self._add_particles(100 + c * CELL_SIZE, 100 + r * CELL_SIZE)
                self.grid[r][c] = 0
            self.score += 10 * GRID_SIZE
            if sound_on:
                pygame.mixer.Sound("data/line_clear.mp3").play()

        for particle in self.explosion_particles[:]:
            particle.update()
            if particle.life <= 0:
                self.explosion_particles.remove(particle)

        self.update_scores()

    def _add_particles(self, x, y):
        for _ in range(15):
            self.explosion_particles.append(ExplosionParticle(x + CELL_SIZE // 2, y + CELL_SIZE // 2))

    def draw_effects(self, screen):
        for particle in self.explosion_particles:
            particle.draw(screen)

    def update_effects(self):
        for particle in self.explosion_particles[:]:
            particle.update()
            if particle.life <= 0:
                self.explosion_particles.remove(particle)

    def save_to_database(self):
        table_name = f"{self.mode}_grid"
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {table_name}")
        for y, row in enumerate(self.grid):
            for x, value in enumerate(row):
                cursor.execute(f"INSERT INTO {table_name} (x, y, value) VALUES (?, ?, ?)", (x, y, value))
        conn.commit()
        conn.close()

    def load_from_database(self):
        table_name = f"{self.mode}_grid"
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(f"SELECT x, y, value FROM {table_name}")
        data = cursor.fetchall()
        for x, y, value in data:
            self.grid[y][x] = value
        conn.close()

    def has_moves(self, shapes):
        for shape in shapes:
            for y in range(GRID_SIZE):
                for x in range(GRID_SIZE):
                    if self.can_place(shape.shape, x, y):
                        return True
        return False

    def reset(self):
        self.grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.score = 0
        self.save_to_database()
        self.update_scores(reset=True)

    def load_scores(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT current_score, high_score FROM scores")
        result = cursor.fetchone()
        if result is None:
            cursor.execute("INSERT INTO scores (current_score, high_score) VALUES (0, 0)")
            conn.commit()
            result = (0, 0)
        conn.close()
        return result

    def update_scores(self, reset=False):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        if reset:
            self.score = 0
        cursor.execute("UPDATE scores SET current_score = ?", (self.score,))
        if self.score > self.high_score:
            self.high_score = self.score
            cursor.execute("UPDATE scores SET high_score = ?", (self.high_score,))
        conn.commit()
        conn.close()

    def save_piece(self, shape, x, y, mode):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        shape_str = str(shape)

        cursor.execute("""
        INSERT INTO pieces (shape, x, y, mode) VALUES (?, ?, ?, ?)
        """, (shape_str, x, y, mode))

        conn.commit()
        conn.close()

    def load_pieces(self, mode):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("""
        SELECT shape, x, y FROM pieces WHERE mode = ?
        """, (mode,))
        rows = cursor.fetchall()
        conn.close()

        loaded_shapes = []
        for row in rows:
            shape_data = eval(row[0])
            x, y = row[1], row[2]
            loaded_shapes.append((Shape(shape_data), (x, y)))

        return loaded_shapes

    def remove_piece(self, shape, x, y, mode):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        shape_str = str(shape)

        cursor.execute("""
        DELETE FROM pieces
        WHERE rowid IN (
            SELECT rowid
            FROM pieces
            WHERE shape = ? AND x = ? AND y = ? AND mode = ?
            LIMIT 1
        )
        """, (shape_str, x, y, mode))

        conn.commit()
        conn.close()


def generate_level(self, level_number):
    required_score = level_number * 200
    num_obstacles = level_number * 4
    obstacles = []

    while len(obstacles) < num_obstacles:
        x, y = random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
        if (x, y) not in obstacles:
            obstacles.append((x, y))

    return {
        "level_number": level_number,
        "required_score": required_score,
        "obstacles": obstacles
    }


class Adventure:
    def __init__(self):
        self.current_level = 1
        self.levels = self.load_levels()
        self.timer_running = False
        self.start_time = 0

    def load_levels(self):
        levels = []
        for level_number in range(1, 11):
            level_data = self.generate_level(level_number)
            levels.append({
                "level_number": level_data["level_number"],
                "required_score": level_data["required_score"],
                "obstacles": level_data["obstacles"],
                "unlocked": level_number == 1
            })
        return levels

    def generate_level(self, level_number):
        required_score = level_number * 200
        num_obstacles = level_number * 4
        obstacles = []

        while len(obstacles) < num_obstacles:
            x, y = random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
            if (x, y) not in obstacles:
                obstacles.append((x, y))

        return {
            "level_number": level_number,
            "required_score": required_score,
            "obstacles": obstacles
        }

    def draw_level_text(self, screen, level_number):
        level_text = font_large.render(f"Level {level_number}", True, WHITE)
        screen.blit(level_text, level_text.get_rect(center=(300, 40)))

    def start_level(self, level_number):
        if not self.levels[level_number - 1]["unlocked"]:
            print(f"Level {level_number} is locked!")
            return False

        print(f"Starting Level {level_number}")
        level_data = self.levels[level_number - 1]
        grid = Grid(obstacles=level_data["obstacles"], mode="adventure")
        required_score = level_data["required_score"]

        for _ in range(4):
            x, y = random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
            if grid.grid[y][x] == 0:
                grid.grid[y][x] = 1

        shapes = [Shape(random.choice(SHAPES)) for _ in range(3)]
        positions = [(600, 100), (600, 250), (600, 400)]
        random.shuffle(positions)
        for i, shape in enumerate(shapes):
            shape.rect.topleft = positions[i]

        dragging_shape = None
        offset_x, offset_y = 0, 0
        clock = pygame.time.Clock()

        while True:

            clock.tick(FPS)
            pygame.mouse.set_visible(True)
            mouse_pos = pygame.mouse.get_pos()
            screen.blit(cursor_image, mouse_pos)
            draw_gradient_background(screen, DARK_BLUE, LIGHT_BLUE)
            back_to_menu_button.draw(screen, pygame.mouse.get_pos())
            self.draw_level_text(screen, level_number)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    grid.save_to_database()
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if back_to_menu_button.is_clicked(pygame.mouse.get_pos(), pygame.mouse.get_pressed()[0]):
                        grid.reset()
                        return False
                    for shape in shapes:
                        if shape.rect.collidepoint(event.pos):
                            dragging_shape = shape
                            offset_x = shape.rect.x - event.pos[0]
                            offset_y = shape.rect.y - event.pos[1]
                            break
                elif event.type == pygame.MOUSEBUTTONUP:
                    if dragging_shape:
                        grid_x = (dragging_shape.rect.x - 100 + CELL_SIZE // 2) // CELL_SIZE
                        grid_y = (dragging_shape.rect.y - 100 + CELL_SIZE // 2) // CELL_SIZE
                        if grid.can_place(dragging_shape.shape, grid_x, grid_y):
                            grid.place(dragging_shape.shape, grid_x, grid_y)
                            shapes.remove(dragging_shape)
                            if not shapes:
                                shapes = [Shape(random.choice(SHAPES)) for _ in range(3)]
                                random.shuffle(positions)
                                for i, shape in enumerate(shapes):
                                    shape.rect.topleft = positions[i]
                        else:
                            print("Invalid position! Try again.")
                        dragging_shape = None

                elif event.type == pygame.MOUSEMOTION and dragging_shape:
                    dragging_shape.rect.x = event.pos[0] + offset_x
                    dragging_shape.rect.y = event.pos[1] + offset_y

            grid.draw()
            for shape in shapes:
                shape.draw(screen)

            if grid.score >= required_score:
                print(f"Level {level_number} completed!")
                self.unlock_next_level(level_number)
                return True

            if not grid.has_moves(shapes):
                print("No moves left! Restarting level...")
                pygame.mixer.Sound("data/game_over.mp3").play()
                show_no_moves_window(grid)

            pygame.display.flip()

    def unlock_next_level(self, level_number):
        next_level = level_number + 1
        if next_level <= len(self.levels):
            self.levels[next_level - 1]["unlocked"] = True

    def draw_timer(self, screen):
        if self.timer_running:
            remaining_time = int(60 - (time.time() - self.start_time))
            timer_text = font_medium.render(f"Time: {remaining_time}", True, WHITE)
            screen.blit(timer_text, timer_text.get_rect(center=(SCREEN_WIDTH - 100, 20)))


SHAPES = [
    [[1, 1], [1, 1]],  # Квадрат
    [[1, 1, 1]],  # Линия горизонтальная
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
]


class Shape:
    def __init__(self, shape):
        self.shape = shape
        self.width = len(shape[0]) * CELL_SIZE
        self.height = len(shape) * CELL_SIZE
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.initial_position = None
        colors = [GREEN, RED, BLUE, PURPLE]
        self.time_color = (colors[(random.randint(0, 3))])

    def set_initial_position(self, position):
        self.initial_position = position
        self.rect.topleft = position

    def reset_to_initial_position(self):
        if self.initial_position:
            self.rect.topleft = self.initial_position

    def draw(self, screen):
        for r, row in enumerate(self.shape):
            for c, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(screen, self.time_color,
                                     (self.rect.x + c * CELL_SIZE, self.rect.y + r * CELL_SIZE, CELL_SIZE, CELL_SIZE))
                    pygame.draw.rect(screen, WHITE,
                                     (self.rect.x + c * CELL_SIZE, self.rect.y + r * CELL_SIZE, CELL_SIZE, CELL_SIZE),
                                     1)


def show_no_moves_window(grid):
    grid.reset()
    retry_button = Button("Retry", SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2, 200, 50, ORANGE, (255, 200, 100))
    menu_button = Button("Menu", SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 70, 200, 50, GREEN, (100, 255, 200))
    running = True

    while running:
        screen.fill(BLACK)
        no_moves_text = font_large.render("No Moves Left!", True, WHITE)
        screen.blit(no_moves_text, no_moves_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100)))

        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        retry_button.draw(screen, mouse_pos)
        menu_button.draw(screen, mouse_pos)

        mouse_pos = pygame.mouse.get_pos()
        screen.blit(cursor_image, mouse_pos)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif mouse_pressed:
                if retry_button.is_clicked(mouse_pos, mouse_pressed):
                    return "retry"
                elif menu_button.is_clicked(mouse_pos, mouse_pressed):
                    return "menu"
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return "retry"
                elif event.key == pygame.K_m:
                    return "menu"


def play_classic():
    clock = pygame.time.Clock()
    grid = Grid()

    loaded_shapes = grid.load_pieces("classic")
    if loaded_shapes:
        shapes = [shape for shape, _ in loaded_shapes]
        positions = [pos for _, pos in loaded_shapes]
        for i, shape in enumerate(shapes):
            shape.rect.topleft = positions[i]
    else:
        shapes = [Shape(random.choice(SHAPES)) for _ in range(3)]
        positions = [(600, 95), (600, 250), (600, 405)]
        random.shuffle(positions)
        for i, shape in enumerate(shapes):
            shape.rect.topleft = positions[i]
            shape.set_initial_position(positions[i])
            grid.save_piece(shape.shape, positions[i][0], positions[i][1], "classic")

    dragging_shape = None
    offset_x = 0
    offset_y = 0

    running = True
    while running:
        clock.tick(FPS)
        if dark_theme:
            draw_gradient_background(screen, DARK_BLUE, BLUE)
        else:
            draw_gradient_background(screen, BLUE, LIGHT_BLUE)

        back_to_menu_button.draw(screen, pygame.mouse.get_pos())

        for cube in background_cubes:
            cube.move()
            cube.draw(screen)

        for event in pygame.event.get():
            if back_to_menu_button.is_clicked(pygame.mouse.get_pos(), pygame.mouse.get_pressed()[0]):
                return
            if event.type == pygame.QUIT:
                grid.save_to_database()
                pygame.quit()
                sys.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                for shape in shapes:
                    if shape.rect.collidepoint(event.pos):
                        dragging_shape = shape
                        offset_x = shape.rect.x - event.pos[0]
                        offset_y = shape.rect.y - event.pos[1]
                        break

            elif event.type == pygame.MOUSEBUTTONUP:
                if dragging_shape:
                    grid_x = (dragging_shape.rect.x - 100 + CELL_SIZE // 2) // CELL_SIZE
                    grid_y = (dragging_shape.rect.y - 100 + CELL_SIZE // 2) // CELL_SIZE

                    if grid.can_place(dragging_shape.shape, grid_x, grid_y):
                        grid.place(dragging_shape.shape, grid_x, grid_y)
                        grid.remove_piece(dragging_shape.shape, dragging_shape.rect.x, dragging_shape.rect.y, "classic")
                        shapes.remove(dragging_shape)

                        if not shapes:
                            shapes = [Shape(random.choice(SHAPES)) for _ in range(3)]
                            random.shuffle(positions)
                            for i, shape in enumerate(shapes):
                                shape.rect.topleft = positions[i]

                        if not grid.has_moves(shapes):
                            shapes = [Shape(random.choice(SHAPES)) for _ in range(3)]
                            random.shuffle(positions)
                            for i, shape in enumerate(shapes):
                                shape.set_initial_position(positions[i])
                                if sound_on:
                                    pygame.mixer.Sound("data/game_over.mp3").play()
                            action = show_no_moves_window(grid)
                            if action == "retry":
                                grid.reset()
                                continue
                            elif action == "menu":
                                return "menu"
                    else:
                        dragging_shape.reset_to_initial_position()

                    dragging_shape = None

            elif event.type == pygame.MOUSEMOTION:
                if dragging_shape:
                    dragging_shape.rect.x = event.pos[0] + offset_x
                    dragging_shape.rect.y = event.pos[1] + offset_y

        grid.update_effects()
        grid.draw()
        grid.draw_effects(screen)

        for shape in shapes:
            shape.draw(screen)

        mouse_pos = pygame.mouse.get_pos()
        screen.blit(cursor_image, mouse_pos)
        pygame.display.flip()


def toggle_music():
    if pygame.mixer.music.get_busy():
        pygame.mixer.music.pause()
    else:
        pygame.mixer.music.unpause()


def open_settings_menu():
    global dark_theme, sound_on
    running = True
    back_button = Button("Back", SCREEN_WIDTH - 250, SCREEN_HEIGHT - 100, 200, 50, ORANGE, (255, 200, 100))
    sound_button = Button(
        "Sound: ON",
        SCREEN_WIDTH // 2 - 150, 300, 300, 70, BLUE, (100, 150, 255)
    )
    theme_toggle_button = Button("Change Theme", SCREEN_WIDTH // 2 - 150, 400, 300, 70, GREEN, (100, 255, 200))

    while running:
        if dark_theme:
            draw_gradient_background(screen, DARK_BLUE, BLUE)
        else:
            draw_gradient_background(screen, BLUE, LIGHT_BLUE)
        for cube in background_cubes:
            cube.move()
            cube.draw(screen)

        settings_text = font_large.render("Settings", True, DARK_GRAY)
        screen.blit(settings_text, settings_text.get_rect(center=(SCREEN_WIDTH // 2, 100)))

        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        sound_button.text = f"Sound ef: {'ON' if sound_on else 'OFF'}"

        back_button.draw(screen, mouse_pos)
        sound_button.draw(screen, mouse_pos)
        theme_toggle_button.draw(screen, mouse_pos)

        screen.blit(cursor_image, mouse_pos)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif mouse_pressed:
                if back_button.is_clicked(mouse_pos, mouse_pressed):
                    running = False
                elif sound_button.is_clicked(mouse_pos, mouse_pressed):
                    sound_on = not sound_on
                    toggle_music()
                    print(f"Sound {'On' if sound_on else 'Off'}")
                elif theme_toggle_button.is_clicked(mouse_pos, mouse_pressed):
                    dark_theme = not dark_theme
                    print(f"Theme {'Dark' if dark_theme else 'Light'}")


def is_first_run():
    if not os.path.exists("data/first_run.txt"):
        with open("data/first_run.txt", "w") as f:
            f.write("Game had been started before.")
        return True
    return False


def show_rules_window():
    running = True
    rules_text = [
        "Rules:",
        "1. Drag shapes onto the grid",
        "2. Fill in rows or columns",
        "3. Destroy blocks to get points",
        "4. Avoid filling the entire grid",
        "5. In Classic mode, get as many points as possible",
        "6. In Adventure fashion, collect the required number",
        "    of points to move to the next level"
    ]

    while running:
        if dark_theme:
            draw_gradient_background(screen, DARK_BLUE, BLUE)
        else:
            draw_gradient_background(screen, BLUE, LIGHT_BLUE)
        for cube in background_cubes:
            cube.move()
            cube.draw(screen)
        back_to_menu_button.draw(screen, pygame.mouse.get_pos())
        y_offset = 100
        for line in rules_text:
            text_surface = font_small.render(line, True, WHITE)
            screen.blit(text_surface, (100, y_offset))
            y_offset += 40

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if back_to_menu_button.is_clicked(pygame.mouse.get_pos(), pygame.mouse.get_pressed()[0]):
                running = False
        mouse_pos = pygame.mouse.get_pos()
        screen.blit(cursor_image, mouse_pos)
        pygame.display.flip()


def open_donate_link():
    import webbrowser
    webbrowser.open("https://www.donationalerts.com/r/gobziii_yt")


def show_tutorial():
    running = True
    while running:
        if dark_theme:
            draw_gradient_background(screen, DARK_BLUE, BLUE)
        else:
            draw_gradient_background(screen, BLUE, LIGHT_BLUE)
        tutorial_text = font_medium.render("Welcome to Block Blast!", True, WHITE)
        instruction_text = font_small.render("Drag and drop blocks to the grid to score points.", True, WHITE)
        continue_text = font_small.render("Press any key to continue...", True, WHITE)

        screen.blit(tutorial_text, tutorial_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50)))
        screen.blit(instruction_text, instruction_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))
        screen.blit(continue_text, continue_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50)))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                running = False


def main():
    clock = pygame.time.Clock()
    adventure = Adventure()
    pygame.mixer.music.load("data/background_music.mp3")
    pygame.mixer.music.set_volume(0.015)
    pygame.mixer.music.play(-1)
    screen.fill(DARK_BLUE if dark_theme else LIGHT_BLUE)

    if is_first_run():
        show_tutorial()

    while True:
        clock.tick(FPS)
        if dark_theme:
            draw_gradient_background(screen, DARK_BLUE, BLUE)
        else:
            draw_gradient_background(screen, BLUE, LIGHT_BLUE)

        for snowflake in snowflakes:
            snowflake.fall()
            snowflake.draw(screen)
        for cube in background_cubes:
            cube.move()
            cube.draw(screen)

        draw_rainbow_text("Cube Cascade", font_large, SCREEN_WIDTH // 2 - 243, 100, WHITE, screen)

        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        for button in buttons:
            button.draw(screen, mouse_pos)
            if button.is_clicked(mouse_pos, mouse_pressed):
                if button.text == "Adventure":
                    level_number = 1
                    while adventure.start_level(level_number):
                        level_number += 1
                elif button.text == "Classic":
                    play_classic()
                elif button.text == "Settings":
                    open_settings_menu()
                elif button.icon == rules_icon:
                    show_rules_window()
                elif button.icon == donate_icon:
                    open_donate_link()

        screen.blit(cursor_image, mouse_pos)
        pygame.display.flip()


if __name__ == "__main__":
    main()
