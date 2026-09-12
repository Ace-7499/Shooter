import pygame
from settings import *

class Player:
    def __init__(self):
        self.width = 50
        self.height = 40
        self.x = WIDTH // 2 - self.width // 2
        self.y = HEIGHT - 80
        self.speed = 6
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def move(self, dx):
        self.x += dx
        if self.x < 0:
            self.x = 0
        elif self.x > WIDTH - self.width:
            self.x = WIDTH - self.width
        self.rect.x = self.x

    def draw(self, surface, color=YELLOW):
        points = [
            (self.x + self.width // 2, self.y),
            (self.x, self.y + self.height),
            (self.x + self.width, self.y + self.height)
        ]
        pygame.draw.polygon(surface, color, points)