import pygame
from settings import *

class Bullet:
    def __init__(self, x, y):
        self.width = 6
        self.height = 12
        self.x = x - self.width // 2
        self.y = y
        self.speed = 7
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def move(self):
        self.y -= self.speed
        self.rect.y = self.y

    def draw(self, surface):
        pygame.draw.rect(surface, WHITE, self.rect)

    def off_screen(self):
        return self.y + self.height < 0