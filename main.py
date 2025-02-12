import sqlite3
import pygame
import sys
import random
import time
import os
import ast

from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, GRID_SIZE, CELL_SIZE, icon_image, screen, sound_on, dark_theme, \
    DB_NAME, WHITE, BLACK, BLUE, RED, ORANGE, GREEN, DARK_BLUE, LIGHT_BLUE, GRAY, DARK_GRAY, PURPLE, YELLOW, \
    font_large, font_medium, font_small, clock_icon, infinity_icon, settings_icon, rules_icon, donate_icon, crown_image, \
    cursor_image, BLOCK_SPRITES
from classes import Button, Snowflake, BackgroundCube, ExplosionParticle

pygame.init()
pygame.display.set_icon(icon_image)
pygame.display.set_caption("Cube Cascade")
pygame.mouse.set_visible(False)
for key in BLOCK_SPRITES:
    BLOCK_SPRITES[key] = pygame.transform.scale(BLOCK_SPRITES[key], (CELL_SIZE, CELL_SIZE))


def initialize_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS classic_grid")
    cursor.execute("DROP TABLE IF EXISTS adventure_grid")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS classic_grid (
        id INTEGER PRIMARY KEY,
        x INTEGER,
        y INTEGER,
        value INTEGER,
        color TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS adventure_grid (
        id INTEGER PRIMARY KEY,
        x INTEGER,
        y INTEGER,
        value INTEGER,
        color TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scores (
        id INTEGER PRIMARY KEY,
        current_score INTEGER DEFAULT 0,
        high_score INTEGER DEFAULT 0
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS levels (
        id INTEGER PRIMARY KEY,
        level_number INTEGER,
        required_score INTEGER,
        unlocked INTEGER DEFAULT 0
    )
    """)

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
back_to_menu_button = Button("Back", SCREEN_WIDTH - 200, 20, 180, 50, ORANGE, (255, 200, 100),
                             animation_speed=0.5)


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


background_cubes = [BackgroundCube() for _ in range(75)]


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
                cell_data = self.grid[row][col]
                x = 100 + col * CELL_SIZE
                y = 100 + row * CELL_SIZE
                if cell_data != 0:
                    if isinstance(cell_data, dict):
                        color = cell_data['color']
                    else:
                        color = "blue"
                    sprite = BLOCK_SPRITES[color]
                    screen.blit(sprite, (x, y))
                else:
                    pygame.draw.rect(screen, GRAY, (x, y, CELL_SIZE, CELL_SIZE))
                    pygame.draw.rect(screen, WHITE, (x, y, CELL_SIZE, CELL_SIZE), 1)

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

    def place(self, shape, x, y, color):
        for r, row in enumerate(shape):
            for c, cell in enumerate(row):
                if cell:
                    self.grid[y + r][x + c] = {
                        'value': 1,
                        'color': color
                    }
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
            for x, cell_data in enumerate(row):
                if isinstance(cell_data, dict):
                    cursor.execute(
                        f"INSERT INTO {table_name} (x, y, value, color) VALUES (?, ?, ?, ?)",
                        (x, y, cell_data['value'], cell_data['color'])
                    )
                else:
                    cursor.execute(
                        f"INSERT INTO {table_name} (x, y, value) VALUES (?, ?, ?)",
                        (x, y, cell_data)
                    )
        conn.commit()
        conn.close()

    def load_from_database(self):
        table_name = f"{self.mode}_grid"
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        try:
            # Пытаемся получить данные с цветом
            cursor.execute(f"SELECT x, y, value, color FROM {table_name}")
        except sqlite3.OperationalError:
            # Если столбца color нет, загружаем без него
            cursor.execute(f"SELECT x, y, value FROM {table_name}")
            data = cursor.fetchall()
            for x, y, value in data:
                self.grid[y][x] = value
            return

        data = cursor.fetchall()
        for x, y, value, color in data:
            if color is not None:
                self.grid[y][x] = {'value': value, 'color': color}
            else:
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

            time_limit = 90 + (i * 5) if i >= 5 else None
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
                    self.show_level_failed(grid)
                    return False

            if dark_theme:
                draw_gradient_background(screen, DARK_BLUE, BLUE)
            else:
                draw_gradient_background(screen, BLUE, LIGHT_BLUE)

            for cube in background_cubes:
                cube.move()
                cube.draw(screen)

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
                            grid.place(dragging_shape.shape, grid_x, grid_y, dragging_shape.time_color)

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
        screen.blit(level_text, (150, 10))

        score_text = font_medium.render(
            f"{grid.score}/{level.required_score}",
            True, GREEN if grid.score >= level.required_score else RED
        )
        screen.blit(score_text, (SCREEN_WIDTH // 2 - 125, 60))

        if time_remaining is not None:
            timer_text = font_medium.render(f"Time: {time_remaining}", True, WHITE)
            screen.blit(timer_text, (SCREEN_WIDTH - 550, 525))

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

        for cube in background_cubes:
            cube.move()
            cube.draw(screen)

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
        self.time_color = random.choice(["blue", "green", "red", "orange"])

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
                    sprite = BLOCK_SPRITES[self.time_color]
                    screen.blit(sprite, (self.rect.x + c * CELL_SIZE, self.rect.y + r * CELL_SIZE))


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
        self.positions = [
            (600, 90),
            (600, 250),
            (600, 410)
        ]
        self.load_game_state()
        self.back_button = Button(
            "Back",
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
        self.grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.shapes = []
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("SELECT x, y, value, color FROM classic_grid")
        for x, y, value, color in cursor.fetchall():
            if value:
                self.grid[y][x] = {'value': value, 'color': color} if color else 1
        cursor.execute("SELECT shape, x, y FROM pieces WHERE mode='classic' AND placed=0")

        for shape_str, x, y in cursor.fetchall():
            try:
                shape_data = ast.literal_eval(shape_str)
                if self.validate_shape(shape_data):
                    new_shape = Shape(shape_data, (x, y))
                    self.shapes.append(new_shape)
            except Exception as e:
                print(f"Error loading shape: {e}")

        cursor.execute("SELECT current_score, high_score FROM scores")
        if res := cursor.fetchone():
            self.score, self.high_score = res

        conn.close()
        if not self.shapes:
            self.generate_new_shapes()

    def validate_shape(self, shape_data):
        if not isinstance(shape_data, list):
            return False
        for row in shape_data:
            if not isinstance(row, list):
                return False
            for cell in row:
                if not isinstance(cell, int):
                    return False
        return True

    def save_game_state(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM classic_grid")
        cursor.execute("DELETE FROM pieces WHERE mode = 'classic'")

        for y, row in enumerate(self.grid):
            for x, cell in enumerate(row):
                if cell != 0:
                    if isinstance(cell, dict):
                        cursor.execute(
                            "INSERT INTO classic_grid (x, y, value, color) VALUES (?, ?, ?, ?)",
                            (x, y, cell['value'], cell['color'])
                        )
                    else:
                        cursor.execute(
                            "INSERT INTO classic_grid (x, y, value) VALUES (?, ?, ?)",
                            (x, y, 1)
                        )
        for shape in self.shapes:
            cursor.execute(
                "INSERT INTO pieces (shape, x, y, mode, placed) VALUES (?, ?, ?, ?, ?)",
                (str(shape.shape), shape.rect.x, shape.rect.y, "classic", 0)
            )

        cursor.execute("UPDATE scores SET current_score=?, high_score=?",
                       (self.score, self.high_score))
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

    def place_shape(self, shape, x, y):
        for r, row in enumerate(shape.shape):
            for c, cell in enumerate(row):
                if cell:
                    self.grid[y + r][x + c] = {
                        'value': 1,
                        'color': shape.time_color
                    }
        self.shapes.remove(shape)
        self.check_lines()
        self.save_game_state()

    def check_lines(self):
        full_rows = [r for r in range(GRID_SIZE) if all(
            cell != 0 for cell in self.grid[r]
        )]
        full_cols = [c for c in range(GRID_SIZE) if all(
            self.grid[r][c] != 0 for r in range(GRID_SIZE)
        )]

        for r in full_rows:
            self.grid[r] = [0] * GRID_SIZE
        for c in full_cols:
            for r in range(GRID_SIZE):
                self.grid[r][c] = 0

        self.score += 10 * GRID_SIZE * (len(full_rows) + len(full_cols))

        if self.score > self.high_score:
            self.high_score = self.score

        self.save_game_state()

    def update_grid_in_db(self, row=None, col=None):
        conn = sqlite3.connect(DB_NAME)
        try:
            cursor = conn.cursor()
            if row is not None:
                cursor.execute(
                    "DELETE FROM classic_grid WHERE y=?",
                    (row,)
                )

            if col is not None:
                cursor.execute(
                    "DELETE FROM classic_grid WHERE x=?",
                    (col,)
                )
            conn.commit()
        except Exception as e:
            conn.rollback()
        finally:
            conn.close()

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
                            self.save_game_state()
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
                if isinstance(self.grid[y][x], dict):
                    color = self.grid[y][x]['color']
                    sprite = BLOCK_SPRITES[color]
                    screen.blit(sprite, (100 + x * CELL_SIZE, 100 + y * CELL_SIZE))
                elif self.grid[y][x] == 1:
                    sprite = BLOCK_SPRITES["blue"]
                    screen.blit(sprite, (100 + x * CELL_SIZE, 100 + y * CELL_SIZE))
                else:
                    pygame.draw.rect(screen, GRAY, (100 + x * CELL_SIZE, 100 + y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
                    pygame.draw.rect(screen, WHITE, (100 + x * CELL_SIZE, 100 + y * CELL_SIZE, CELL_SIZE, CELL_SIZE), 1)

        for shape in self.shapes:
            shape.draw(screen)

        if self.dragging_shape:
            self.dragging_shape.draw(screen)

        score_text = font_medium.render(f"Score: {self.score}", True, ORANGE)
        screen.blit(score_text, (10, 50))
        high_score_text = font_medium.render(f"High score: {self.high_score}", True, RED)
        screen.blit(high_score_text, (10, 10))
        self.back_button.draw(screen, pygame.mouse.get_pos())
        mouse_pos = pygame.mouse.get_pos()
        screen.blit(cursor_image, mouse_pos)

    def has_moves_left(self):
        for shape in self.shapes:
            for y in range(GRID_SIZE - len(shape.shape) + 1):
                for x in range(GRID_SIZE - len(shape.shape[0]) + 1):
                    if self.can_place(shape.shape, x, y):
                        return True
        return False


def play_classic():
    classic_mode = ClassicMode()
    classic_mode.load_game_state()
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


def open_settings_menu():
    global dark_theme, sound_on, current_language
    running = True
    back_button = Button("Back", SCREEN_WIDTH - 250, SCREEN_HEIGHT - 100, 200, 50, ORANGE, (255, 200, 100))
    sound_button = Button(
        "Sound: ON",
        SCREEN_WIDTH // 2 - 150, 300, 300, 70, BLUE, (100, 150, 255)
    )
    theme_toggle_button = Button("Change Theme", SCREEN_WIDTH // 2 - 150, 400, 300, 70, GREEN,
                                 (100, 255, 200))
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
        sound_button.text = f"Sound: {'ON' if sound_on else 'OFF'}"
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
                    print(f"Sound: {'ON' if sound_on else 'OFF'}")
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
                    adventure_mode = AdventureMode()
                    level_selection_menu(adventure_mode)
                    if adventure_mode.current_grid:
                        adventure_mode.current_grid.reset()
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

