import pygame
import random
from settings import *

class PowerUp:
    def __init__(self, force_type=None):
        self.width = 28
        self.height = 28
        if force_type is not None:
            self.type = force_type
        else:
            self.type = random.choice([POWERUP_RAPID, POWERUP_DOUBLE])
        # 从顶部掉落
        self.x = random.randint(0, WIDTH - self.width)
        self.y = random.randint(-100, -40)
        self.speed = 3
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def move(self):
        self.y += self.speed
        self.rect.y = self.y

    def draw(self, surface):
        if self.type == POWERUP_RAPID:
            color = BLUE
            letter = "R"
        elif self.type == POWERUP_DOUBLE:
            color = GREEN
            letter = "D"
        else:  # POWERUP_MISSILE
            color = PURPLE
            letter = "M"
        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        font = pygame.font.SysFont("Arial", 18, bold=True)
        text = font.render(letter, True, WHITE)
        text_rect = text.get_rect(center=self.rect.center)
        surface.blit(text, text_rect)

    def off_screen(self):
        return self.y > HEIGHT