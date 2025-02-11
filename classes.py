import random
import sqlite3
import sys
import time

import pygame

from settings import WHITE, font_medium, SCREEN_WIDTH, SCREEN_HEIGHT, FPS, ORANGE, RED, YELLOW, DB_NAME, GRID_SIZE, \
    GRAY, BLUE, CELL_SIZE, screen, crown_image, sound_on, font_large, cursor_image, GREEN, SHAPES, DARK_BLUE, \
    LIGHT_BLUE, dark_theme


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



