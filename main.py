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
current_language = "English"

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
            mode TEXT NOT NULL,
            placed INTEGER DEFAULT 0
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


def get_text(text):
    if current_language == "Russian":
        translations = {
            "Level": "Уровень",
            "Cube Cascade": "  Куб Каскад",
            "Back": "Назад",
            "Retry": "Повторить",
            "Menu": "Меню",
            "Settings": "Настройки",
            "Sound: ON": "Звук: ВКЛ",
            "Sound: OFF": "Звук: ВЫКЛ",
            "Change Theme": "Сменить тему",
            "Language: English": "Язык: Русский",
            "Rules": "Правила",
            "Donate": "Поддержать",
            "Adventure": "Приключение",
            "Classic": "Классика",
            "No Moves Left!": "Нет ходов!",
            "Welcome to Block Blast!": "Добро пожаловать в Block Blast!",
            "Drag and drop blocks to the grid to score points.":
                "Перетаскивайте блоки на сетку, чтобы набирать очки.",
            "Press any key to continue...": "Нажмите любую клавишу, чтобы продолжить...",
            "Theme Dark": "Тема Тёмная",
            "Theme Light": "Тема Светлая",
            "Language changed to English": "Язык изменён на Английский",
            "Language changed to Russian": "Язык изменён на Русский"
        }
        return translations.get(text, text)
    elif current_language == "English":
        translations = {
            "Уровень": "Level",
            "Куб Каскад": "Cube Cascade",
            "Назад": "Back",
            "Повторить": "Retry",
            "Меню": "Menu",
            "Настройки": "Settings",
            "Звук: ВКЛ": "Sound: ON",
            "Звук: ВЫКЛ": "Sound: OFF",
            "Сменить тему": "Change Theme",
            "Язык: Русский": "Language: English",
            "Правила": "Rules",
            "Поддержать": "Donate",
            "Приключение": "Adventure",
            "Классика": "Classic",
            "Нет ходов!": "No Moves Left!",
            "Добро пожаловать в Block Blast!": "Welcome to Block Blast!",
            "Перетаскивайте блоки на сетку, чтобы набирать очки.":
                "Drag and drop blocks to the grid to score points.",
            "Нажмите любую клавишу, чтобы продолжить...": "Press any key to continue...",
            "Тема Тёмная": "Theme Dark",
            "Тема Светлая": "Theme Light",
            "Язык изменён на Английский": "Language changed to English",
            "Язык изменён на Русский": "Language changed to Russian"
        }
        return translations.get(text, text)
    return text


buttons = [
    Button("Adventure", SCREEN_WIDTH // 2 - 150, 200, 300, 70, ORANGE, (255, 200, 100), icon=clock_icon,
           animation_speed=0.5),
    Button("Classic", SCREEN_WIDTH // 2 - 150, 300, 300, 70, GREEN, (100, 255, 200), icon=infinity_icon,
           animation_speed=0.5),
    Button("Settings", SCREEN_WIDTH // 2 - 150, 500, 300, 70, BLUE, (100, 150, 255), icon=settings_icon,
           animation_speed=0.5),
    Button("", SCREEN_WIDTH // 2 - 150, 400, 125, 70, PURPLE, (150, 100, 200), icon=rules_icon, animation_speed=0.5),
    Button("", SCREEN_WIDTH // 2 + 25, 400, 125, 70, PURPLE, (150, 100, 200), icon=donate_icon, animation_speed=0.5)
]

back_to_menu_button = Button(get_text("Back"), SCREEN_WIDTH - 200, 20, 180, 50, ORANGE, (255, 200, 100),
                             animation_speed=0.5)


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
        self.reset(obstacles, mode)

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

    def reset(self, obstacles=None, mode="classic"):
        self.grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        if obstacles:
            for x, y in obstacles:
                self.grid[y][x] = 1
        self.score = 0
        self.save_to_database()

    def load_high_score(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT high_score FROM scores")
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 0

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


class AdventureLevel:
    def __init__(self, number, required_score, obstacles, time_limit=None):
        self.number = number
        self.required_score = required_score
        self.obstacles = obstacles
        self.time_limit = time_limit
        self.unlocked = False
        self.completed = False


class AdventureMode:
    def __init__(self):
        self.levels = []
        self.current_level = 0
        self.current_grid = None
        self.generate_levels()
        self.load_progress()
        self.timer_active = False
        self.start_time = 0

        self.positions = [
            (600, 90),
            (600, 250),
            (600, 410)
        ]

    def has_moves_left(self):
        for shape in self.shapes:
            for y in range(GRID_SIZE - len(shape.shape) + 1):
                for x in range(GRID_SIZE - len(shape.shape[0]) + 1):
                    if self.can_place(shape.shape, x, y):
                        return True
        return False

    def generate_shapes(self, count):
        shapes = []
        shape_pool = SHAPES[:]
        if self.current_level >= 3:
            shape_pool += SHAPES[3:]
        if self.current_level >= 6:
            shape_pool += SHAPES[6:]

        for i in range(count):
            shape_data = random.choice(shape_pool)
            shape = Shape(shape_data, self.positions[i])
            shapes.append(shape)

        return shapes

    def generate_levels(self):
        for i in range(1, 11):
            obstacles = []
            num_obstacles = min(i * 2, 15)
            while len(obstacles) < num_obstacles:
                pos = (random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1))
                if pos not in obstacles:
                    obstacles.append(pos)

            time_limit = 60 + (i * 5) if i >= 5 else None
            level = AdventureLevel(
                number=i,
                required_score=i * 250,
                obstacles=obstacles,
                time_limit=time_limit
            )
            self.levels.append(level)

        self.levels[0].unlocked = True

    def load_progress(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT level_number, unlocked FROM levels")
        for level_num, unlocked in cursor.fetchall():
            if level_num - 1 < len(self.levels):
                self.levels[level_num - 1].unlocked = bool(unlocked)
        conn.close()

    def unlock_next_level(self):
        next_level = self.current_level + 1
        if next_level < len(self.levels):
            self.levels[next_level].unlocked = True
            self.save_progress()

    def save_progress(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        for i, level in enumerate(self.levels):
            cursor.execute("""
                INSERT OR REPLACE INTO levels 
                (id, level_number, unlocked)
                VALUES (?, ?, ?)
            """, (i + 1, level.number, int(level.unlocked)))
        conn.commit()
        conn.close()

    def start_level(self, level_number):
        if not 0 <= level_number < len(self.levels):
            return False

        level = self.levels[level_number]
        if not level.unlocked:
            return False

        self.current_grid = Grid(obstacles=level.obstacles, mode="adventure")

        self.current_level = level_number
        self.timer_active = bool(level.time_limit)
        self.start_time = time.time()

        result = self.run_level(self.current_grid, level)

        self.current_grid.reset()
        return result

    def run_level(self, grid, level):
        shapes = self.generate_shapes(3)

        positions = [
            (600, 90),
            (600, 250),
            (600, 410)
        ]

        for i, shape in enumerate(shapes):
            shape.rect.topleft = positions[i]
            shape.set_initial_position(positions[i])
        clock = pygame.time.Clock()
        running = True
        success = False
        dragging_shape = None
        offset_x, offset_y = 0, 0

        while running:
            time_remaining = None
            if self.timer_active:
                elapsed = time.time() - self.start_time
                time_remaining = max(0, level.time_limit - int(elapsed))
                if time_remaining <= 0:
                    self.handle_timeout(grid)
                    return False

            screen.fill(DARK_BLUE if dark_theme else LIGHT_BLUE)
            grid.draw()
            self.draw_ui(level, time_remaining, grid)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()

                    for shape in shapes:
                        if shape.rect.collidepoint(mouse_pos):
                            dragging_shape = shape
                            offset_x = shape.rect.x - mouse_pos[0]
                            offset_y = shape.rect.y - mouse_pos[1]
                            break

                if event.type == pygame.MOUSEBUTTONUP:
                    if dragging_shape:
                        grid_x = (dragging_shape.rect.x - 100 + CELL_SIZE // 2) // CELL_SIZE
                        grid_y = (dragging_shape.rect.y - 100 + CELL_SIZE // 2) // CELL_SIZE

                        if grid.can_place(dragging_shape.shape, grid_x, grid_y):
                            grid.place(dragging_shape.shape, grid_x, grid_y)

                            shapes.remove(dragging_shape)

                            if not shapes:
                                shapes = self.generate_shapes(3)
                                for i, shape in enumerate(shapes):
                                    shape.rect.topleft = positions[i]
                                    shape.set_initial_position(positions[i])
                        else:
                            dragging_shape.reset_to_initial_position()

                        dragging_shape = None

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    if SCREEN_WIDTH - 100 <= mouse_pos[0] <= SCREEN_WIDTH - 20 and 20 <= mouse_pos[1] <= 50:
                        running = False
                        return "menu"

                if event.type == pygame.MOUSEMOTION and dragging_shape:
                    dragging_shape.rect.x = event.pos[0] + offset_x
                    dragging_shape.rect.y = event.pos[1] + offset_y

            for shape in shapes:
                shape.draw(screen)

            if dragging_shape:
                dragging_shape.draw(screen)

            if grid.score >= level.required_score:
                level.completed = True
                self.unlock_next_level()
                success = True
                running = False
                self.show_level_complete(level)

            if not grid.has_moves(shapes):
                self.show_level_failed(level)
                running = False

            mouse_pos = pygame.mouse.get_pos()
            screen.blit(cursor_image, mouse_pos)

            pygame.display.flip()
            clock.tick(FPS)

        return success

    def load_global_record(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT high_score FROM scores")
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 0

    def generate_shapes(self, count):
        shapes = []
        for pos in self.positions:
            shape = Shape(random.choice(SHAPES), pos)
            shapes.append(shape)
        return shapes

    def draw_ui(self, level, time_remaining, grid):
        back_to_menu_button.draw(screen, pygame.mouse.get_pos())
        level_text = font_medium.render(f"Level {level.number}", True, ORANGE)
        screen.blit(level_text, (130, 10))

        score_text = font_medium.render(
            f"{grid.score}/{level.required_score}",
            True, GREEN if grid.score >= level.required_score else RED
        )
        screen.blit(score_text, (SCREEN_WIDTH // 2 - 125, 60))

        if time_remaining is not None:
            timer_text = font_medium.render(f"Time: {time_remaining}", True, WHITE)
            screen.blit(timer_text, (SCREEN_WIDTH - 200, 20))

    def show_level_complete(self, level):
        particles = []
        start_time = time.time()
        show_message = True
        clock = pygame.time.Clock()

        next_level_btn = Button(
            "Menu",
            SCREEN_WIDTH // 2 - 100,
            SCREEN_HEIGHT // 2 + 50,
            200, 50,
            GREEN, (100, 255, 200)
        )

        while show_message:
            if random.random() < 0.3:
                particles.append(ExplosionParticle(
                    random.randint(100, SCREEN_WIDTH - 100),
                    random.randint(100, SCREEN_HEIGHT // 2),
                ))

            screen.fill((0, 0, 0, 0))
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            screen.blit(overlay, (0, 0))

            for p in particles[:]:
                p.update()
                p.draw(screen)
                if p.life <= 0:
                    particles.remove(p)

            text = font_large.render("Level Complete!", True, GREEN)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
            screen.blit(text, text_rect)

            next_level_btn.draw(screen, pygame.mouse.get_pos())

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if next_level_btn.is_clicked(pygame.mouse.get_pos(), True):
                        show_message = False

            mouse_pos = pygame.mouse.get_pos()
            screen.blit(cursor_image, mouse_pos)

            pygame.display.flip()
            clock.tick(FPS)

    def show_level_failed(self, level):
        particles = []
        start_time = time.time()
        show_message = True
        clock = pygame.time.Clock()

        retry_btn = Button(
            "Retry",
            SCREEN_WIDTH // 2 - 110,
            SCREEN_HEIGHT // 2 + 50,
            100, 50,
            ORANGE, (255, 200, 100)
        )

        menu_btn = Button(
            "Menu",
            SCREEN_WIDTH // 2 + 10,
            SCREEN_HEIGHT // 2 + 50,
            100, 50,
            RED, (255, 100, 100)
        )

        if sound_on:
            pygame.mixer.Sound("data/game_over.mp3").play()

        while show_message:
            if random.random() < 0.2:
                particles.append(SmokeParticle(
                    random.randint(100, SCREEN_WIDTH - 100),
                    SCREEN_HEIGHT // 2 + 50,
                ))

            screen.fill((0, 0, 0, 0))
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((50, 0, 0, 150))
            screen.blit(overlay, (0, 0))

            for p in particles[:]:
                p.update()
                p.draw(screen)
                if p.life <= 0:
                    particles.remove(p)

            text = font_large.render("Failed!", True, RED)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
            screen.blit(text, text_rect)

            retry_btn.draw(screen, pygame.mouse.get_pos())
            menu_btn.draw(screen, pygame.mouse.get_pos())

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if retry_btn.is_clicked(pygame.mouse.get_pos(), True):
                        show_message = False
                        self.start_level(self.current_level)
                    elif menu_btn.is_clicked(pygame.mouse.get_pos(), True):
                        show_message = False

            mouse_pos = pygame.mouse.get_pos()
            screen.blit(cursor_image, mouse_pos)

            pygame.display.flip()
            clock.tick(FPS)


class SmokeParticle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = random.randint(8, 15)
        self.life = 100
        self.speed = [random.uniform(-0.5, 0.5), random.uniform(-2, -1)]
        self.color = (100, 100, 100, 200)

    def update(self):
        self.x += self.speed[0]
        self.y += self.speed[1]
        self.life -= 2
        self.size *= 0.98
        self.color = (
            self.color[0],
            self.color[1],
            self.color[2],
            max(0, self.color[3] - 3)
        )

    def draw(self, screen):
        pygame.draw.circle(
            screen,
            self.color,
            (int(self.x), int(self.y)),
            int(self.size)
        )


def level_selection_menu(adventure):
    clock = pygame.time.Clock()
    running = True

    level_buttons = []
    button_width = 150
    button_height = 70
    padding = 20
    start_x = (SCREEN_WIDTH - (3 * button_width + 2 * padding)) // 2
    start_y = 150

    for i, level in enumerate(adventure.levels):
        row = i // 3
        col = i % 3
        x = start_x + col * (button_width + padding)
        y = start_y + row * (button_height + padding)

        if level.completed:
            color = GREEN
            hover_color = (100, 255, 100)
        elif level.unlocked:
            color = ORANGE
            hover_color = (255, 200, 100)
        else:
            color = DARK_GRAY
            hover_color = DARK_GRAY

        button = Button(
            text=f"Level {level.number}",
            x=x,
            y=y,
            width=button_width,
            height=button_height,
            color=color,
            hover_color=hover_color,
            animation_speed=0.2
        )
        level_buttons.append((button, level))

    back_button = Button(
        text="Back",
        x=SCREEN_WIDTH - 200,
        y=SCREEN_HEIGHT - 80,
        width=180,
        height=50,
        color=BLUE,
        hover_color=(100, 150, 255)
    )

    while running:
        clock.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        if dark_theme:
            draw_gradient_background(screen, DARK_BLUE, BLUE)
        else:
            draw_gradient_background(screen, BLUE, LIGHT_BLUE)

        title_text = font_large.render("Select Level", True, WHITE)
        screen.blit(title_text, title_text.get_rect(center=(SCREEN_WIDTH//2, 80)))

        for button, level in level_buttons:
            button.draw(screen, mouse_pos)
            if level.completed:
                screen.blit(crown_image, (button.rect.right - 40, button.rect.top + 5))
            if button.is_clicked(mouse_pos, mouse_pressed) and level.unlocked:
                adventure.start_level(level.number - 1)
                running = False

        back_button.draw(screen, mouse_pos)
        if back_button.is_clicked(mouse_pos, mouse_pressed):
            running = False

        screen.blit(cursor_image, mouse_pos)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        pygame.display.flip()


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
    [[1, 1, 1], [0, 0, 1]],  # Крюк4
]


class Shape:
    def __init__(self, shape, initial_position):
        self.shape = shape
        self.width = len(shape[0]) * CELL_SIZE
        self.height = len(shape) * CELL_SIZE
        self.rect = pygame.Rect(
            initial_position[0],
            initial_position[1],
            self.width,
            self.height
        )
        self.initial_position = initial_position
        self.time_color = random.choice([BLUE, GREEN, ORANGE, RED])

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


def show_no_moves_window():
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


class ClassicMode:
    def __init__(self):
        self.grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.shapes = []
        self.placed_shapes = []
        self.dragging_shape = None
        self.offset_x, self.offset_y = 0, 0
        self.score = 0
        self.high_score = self.load_high_score()
        self.positions = [(600, 100), (600, 250), (600, 400)]
        self.load_game_state()

        self.back_button = Button(
            get_text("Back"),
            SCREEN_WIDTH - 200,
            20,
            180,
            50,
            ORANGE,
            (255, 200, 100)
        )

    def load_high_score(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT high_score FROM scores")
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 0

    def load_game_state(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("SELECT x, y, value FROM classic_grid")
        for x, y, value in cursor.fetchall():
            self.grid[y][x] = value

        cursor.execute("SELECT shape, x, y FROM pieces WHERE mode = 'classic' AND placed = 1")
        for shape_str, x, y in cursor.fetchall():
            shape = eval(shape_str)
            self.placed_shapes.append((shape, (x, y)))

        cursor.execute("SELECT shape, x, y FROM pieces WHERE mode = 'classic' AND placed = 0")
        for shape_str, x, y in cursor.fetchall():
            shape = eval(shape_str)
            self.shapes.append(Shape(shape, (x, y)))

        conn.close()

        if not self.shapes:
            self.generate_new_shapes()

    def save_game_state(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM classic_grid")
        for y, row in enumerate(self.grid):
            for x, value in enumerate(row):
                cursor.execute("INSERT INTO classic_grid (x, y, value) VALUES (?, ?, ?)", (x, y, value))

        cursor.execute("DELETE FROM pieces WHERE mode = 'classic' AND placed = 1")
        for shape, (x, y) in self.placed_shapes:
            cursor.execute("INSERT INTO pieces (shape, x, y, mode, placed) VALUES (?, ?, ?, ?, ?)",
                           (str(shape), x, y, "classic", 1))

        cursor.execute("DELETE FROM pieces WHERE mode = 'classic' AND placed = 0")
        for shape in self.shapes:
            cursor.execute("INSERT INTO pieces (shape, x, y, mode, placed) VALUES (?, ?, ?, ?, ?)",
                           (str(shape.shape), shape.rect.x, shape.rect.y, "classic", 0))

        cursor.execute("UPDATE scores SET current_score = ?, high_score = ?", (self.score, self.high_score))

        conn.commit()
        conn.close()

    def generate_new_shapes(self):
        if not self.shapes:
            for pos in self.positions:
                shape = Shape(random.choice(SHAPES), pos)
                self.shapes.append(shape)

    def can_place(self, shape, x, y):
        for r, row in enumerate(shape):
            for c, cell in enumerate(row):
                if cell:
                    grid_x = x + c
                    grid_y = y + r
                    if grid_x >= GRID_SIZE or grid_y >= GRID_SIZE or grid_x < 0 or grid_y < 0 or self.grid[grid_y][grid_x] != 0:
                        return False
        return True

    def has_moves_left(self):
        for shape in self.shapes:
            for y in range(GRID_SIZE - len(shape.shape) + 1):
                for x in range(GRID_SIZE - len(shape.shape[0]) + 1):
                    if self.can_place(shape.shape, x, y):
                        return True
        return False

    def place_shape(self, shape, x, y):
        for r, row in enumerate(shape.shape):
            for c, cell in enumerate(row):
                if cell:
                    self.grid[y + r][x + c] = 1
        self.placed_shapes.append((shape.shape, (x, y)))
        self.shapes.remove(shape)
        self.check_lines()
        self.save_game_state()

    def check_lines(self):
        full_rows = [r for r in range(GRID_SIZE) if all(self.grid[r])]
        full_cols = [c for c in range(GRID_SIZE) if all(self.grid[r][c] for r in range(GRID_SIZE))]

        for r in full_rows:
            for c in range(GRID_SIZE):
                self.grid[r][c] = 0
            self.score += 10 * GRID_SIZE

        for c in full_cols:
            for r in range(GRID_SIZE):
                self.grid[r][c] = 0
            self.score += 10 * GRID_SIZE

        if self.score > self.high_score:
            self.high_score = self.score

    def reset_game(self):
        self.grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.shapes = []
        self.placed_shapes = []
        self.score = 0
        self.generate_new_shapes()
        self.save_game_state()

    def run(self, screen):
        clock = pygame.time.Clock()
        running = True

        while running:
            clock.tick(FPS)
            if dark_theme:
                draw_gradient_background(screen, DARK_BLUE, BLUE)
            else:
                draw_gradient_background(screen, BLUE, LIGHT_BLUE)

            for cube in background_cubes:
                cube.move()
                cube.draw(screen)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.save_game_state()
                    pygame.quit()
                    sys.exit()

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()

                    if self.back_button.is_clicked(mouse_pos, True):
                        self.save_game_state()
                        return "menu"

                    for shape in self.shapes:
                        if shape.rect.collidepoint(mouse_pos):
                            self.dragging_shape = shape
                            self.offset_x = shape.rect.x - mouse_pos[0]
                            self.offset_y = shape.rect.y - mouse_pos[1]
                            break

                elif event.type == pygame.MOUSEBUTTONUP:
                    if self.dragging_shape:
                        grid_x = (self.dragging_shape.rect.x - 100 + CELL_SIZE // 2) // CELL_SIZE
                        grid_y = (self.dragging_shape.rect.y - 100 + CELL_SIZE // 2) // CELL_SIZE

                        if self.can_place(self.dragging_shape.shape, grid_x, grid_y):
                            self.place_shape(self.dragging_shape, grid_x, grid_y)
                            self.generate_new_shapes()

                            if not self.has_moves_left():
                                self.reset_game()
                                if show_no_moves_window() == 'menu':
                                    return 'menu'
                        else:
                            self.dragging_shape.reset_to_initial_position()

                        self.dragging_shape = None

                elif event.type == pygame.MOUSEMOTION and self.dragging_shape:
                    self.dragging_shape.rect.x = event.pos[0] + self.offset_x
                    self.dragging_shape.rect.y = event.pos[1] + self.offset_y

            self.draw(screen)
            pygame.display.flip()

    def draw(self, screen):
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                color = BLUE if self.grid[y][x] else GRAY
                rect = pygame.Rect(100 + x * CELL_SIZE, 100 + y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(screen, color, rect)
                pygame.draw.rect(screen, WHITE, rect, 1)

        for shape in self.shapes:
            shape.draw(screen)

        if self.dragging_shape:
            self.dragging_shape.draw(screen)

        score_text = font_medium.render(f"Score: {self.score}", True, ORANGE)
        screen.blit(score_text, (10, 10))

        high_score_text = font_medium.render(f"High score: {self.high_score}", True, GREEN)
        screen.blit(high_score_text, (10, 50))

        self.back_button.draw(screen, pygame.mouse.get_pos())

        mouse_pos = pygame.mouse.get_pos()
        screen.blit(cursor_image, mouse_pos)


def play_classic():
    classic_mode = ClassicMode()
    classic_mode.run(screen)


def migrate_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute("ALTER TABLE pieces ADD COLUMN placed INTEGER DEFAULT 0")
    except sqlite3.OperationalError as e:
        print("Column already exists:", e)

    conn.commit()
    conn.close()


initialize_database()
migrate_database()


def toggle_music():
    if pygame.mixer.music.get_busy():
        pygame.mixer.music.pause()
    else:
        pygame.mixer.music.unpause()


def change_language(language):
    global current_language
    current_language = language


def open_settings_menu():
    global dark_theme, sound_on, current_language
    running = True
    back_button = Button(get_text("Back"), SCREEN_WIDTH - 250, SCREEN_HEIGHT - 100, 200, 50, ORANGE, (255, 200, 100))
    sound_button = Button(get_text(
        "Sound: ON"),
        SCREEN_WIDTH // 2 - 150, 300, 300, 70, BLUE, (100, 150, 255)
    )
    theme_toggle_button = Button(get_text("Change Theme"), SCREEN_WIDTH // 2 - 150, 400, 300, 70, GREEN,
                                 (100, 255, 200))
    language_button = Button(get_text("Language: English"), SCREEN_WIDTH // 2 - 150, 200, 300, 70, BLUE,
                             (100, 150, 255))

    while running:
        if dark_theme:
            draw_gradient_background(screen, DARK_BLUE, BLUE)
        else:
            draw_gradient_background(screen, BLUE, LIGHT_BLUE)
        for cube in background_cubes:
            cube.move()
            cube.draw(screen)

        settings_text = font_large.render(get_text("Settings"), True, DARK_GRAY)
        screen.blit(settings_text, settings_text.get_rect(center=(SCREEN_WIDTH // 2, 100)))

        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        sound_button.text = get_text(f"Sound: {'ON' if sound_on else 'OFF'}")

        back_button.draw(screen, mouse_pos)
        sound_button.draw(screen, mouse_pos)
        theme_toggle_button.draw(screen, mouse_pos)
        language_button.draw(screen, mouse_pos)

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
                    print(get_text(f"Sound: {'ON' if sound_on else 'OFF'}"))
                elif theme_toggle_button.is_clicked(mouse_pos, mouse_pressed):
                    dark_theme = not dark_theme
                    print(get_text(f"Theme {'Dark' if dark_theme else 'Light'}"))
                elif language_button.is_clicked(mouse_pos, mouse_pressed):
                    print(get_text(f"Language changed to {current_language}"))
                    if current_language == "English":
                        change_language("Russian")
                        language_button.text = get_text("Language: English")
                        back_button.text = get_text("Back")
                        sound_button.text = get_text("Sound: ON")
                        theme_toggle_button.text = get_text("Change Theme")
                        for button in buttons:
                            if button.text == "Adventure":
                                button.text = get_text("Adventure")
                            elif button.text == "Classic":
                                button.text = get_text("Classic")
                            elif button.text == "Settings":
                                button.text = get_text("Settings")
                            elif button.text == "Rules":
                                button.text = get_text("Rules")
                            elif button.text == "Donate":
                                button.text = get_text("Donate")
                else:
                    change_language("English")
                    language_button.text = get_text("Language: English")
                    back_button.text = get_text("Back")
                    sound_button.text = get_text("Sound: ON")
                    theme_toggle_button.text = get_text("Change Theme")
                    for button in buttons:
                        if button.text == "Приключение":
                            button.text = get_text("Adventure")
                        elif button.text == "Классика":
                            button.text = get_text("Classic")
                        elif button.text == "Настройки":
                            button.text = get_text("Settings")
                        elif button.text == "Правила":
                            button.text = get_text("Rules")
                        elif button.text == "Поддержать":
                            button.text = get_text("Donate")


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

    rules_text_ru = [
        "Правила:",
        "1. Перетащите фигуры на сетку",
        "2. Заполните строки или столбцы",
        "3. Уничтожьте блоки, чтобы получить очки",
        "4. Избегайте заполнения всей сетки",
        "5. В режиме Классика наберите как можно больше очков",
        "6. В режиме Приключения соберите необходимое количество",
        "     очков, чтобы перейти на следующий уровень"
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
        if current_language == 'English':
            for line in rules_text:
                text_surface = font_small.render(line, True, WHITE)
                screen.blit(text_surface, (100, y_offset))
                y_offset += 40
        else:
            for line in rules_text_ru:
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
    adventure_mode = AdventureMode()
    grid = Grid
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

        draw_rainbow_text(get_text("Cube Cascade"), font_large, SCREEN_WIDTH // 2 - 243, 100, WHITE, screen)

        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        for button in buttons:
            button.draw(screen, mouse_pos)
            if button.is_clicked(mouse_pos, mouse_pressed):
                if button.text == "Adventure" or button.text == "Приключение":
                    adventure_mode = AdventureMode()
                    level_selection_menu(adventure_mode)
                    if adventure_mode.current_grid:
                        adventure_mode.current_grid.reset()
                elif button.text == "Classic" or button.text == "Классика":
                    play_classic()
                elif button.text == "Settings" or button.text == "Настройки":
                    open_settings_menu()
                elif button.icon == rules_icon:
                    show_rules_window()
                elif button.icon == donate_icon:
                    open_donate_link()

        screen.blit(cursor_image, mouse_pos)
        pygame.display.flip()


if __name__ == "__main__":
    main()

