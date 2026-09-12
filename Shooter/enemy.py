import pygame
import random
import math
from settings import *

class Enemy:
    def __init__(self, enemy_type=ENEMY_NORMAL):
        self.type = enemy_type
        self.width = 45
        self.height = 35
        self.x = random.randint(0, WIDTH - self.width)
        self.y = random.randint(-100, -40)
        self.hp = 1
        self.max_hp = 1
        self.flash_timer = 0

        # 使用专属颜色
        self.color = ENEMY_COLORS.get(enemy_type, RED)

        if self.type == ENEMY_HOMING:
            self.speed = 2.0
        elif self.type == ENEMY_DRUNK:
            self.circle_center_x = self.x
            self.circle_center_y = self.y
            self.circle_radius = random.randint(50, 80)
            self.angle = random.uniform(0, 2 * math.pi)
            self.angular_speed = random.uniform(0.03, 0.06)
            self.fall_speed = random.uniform(1.5, 3.0)
        elif self.type == ENEMY_TORNADO:
            self.speed = 5
            self.wave_amplitude = random.uniform(0.5, 0.9)
            self.wave_frequency = random.uniform(0.08, 0.12)
            self.wave_timer = random.uniform(0, 2 * math.pi)
        elif self.type == ENEMY_HEAVY:
            self.speed = random.uniform(1.0, 2.0)
            self.hp = 3
            self.max_hp = 3
            self.drift = random.uniform(-0.5, 0.5)
        else:  # NORMAL
            self.speed = random.randint(3, 7)

        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def move(self, target_x=None, target_y=None):
        if self.type == ENEMY_HOMING:
            if target_x is not None and target_y is not None:
                dx = target_x - self.x
                dy = target_y - self.y
                dist = math.hypot(dx, dy)
                if dist != 0:
                    dx /= dist
                    dy /= dist
                self.x += dx * self.speed
                self.y += dy * self.speed
                self.speed += 0.05
                if self.speed > 10:
                    self.speed = 10
        elif self.type == ENEMY_DRUNK:
            self.circle_center_y += self.fall_speed
            self.angle += self.angular_speed
            self.x = self.circle_center_x + math.cos(self.angle) * self.circle_radius
            self.y = self.circle_center_y + math.sin(self.angle) * self.circle_radius
        elif self.type == ENEMY_TORNADO:
            if target_x is not None and target_y is not None:
                desired_angle = math.atan2(target_y - self.y, target_x - self.x)
                self.wave_timer += 1
                offset = self.wave_amplitude * math.sin(self.wave_frequency * self.wave_timer)
                move_angle = desired_angle + offset
                self.x += math.cos(move_angle) * self.speed
                self.y += math.sin(move_angle) * self.speed
            else:
                self.y += self.speed
        elif self.type == ENEMY_HEAVY:
            self.y += self.speed
            self.x += self.drift
            if self.x < 0 or self.x > WIDTH - self.width:
                self.drift *= -1
        else:  # NORMAL
            self.y += self.speed

        self.rect.x = self.x
        self.rect.y = self.y

        if self.flash_timer > 0:
            self.flash_timer -= 1

    def take_damage(self):
        self.hp -= 1
        self.flash_timer = 5
        return self.hp <= 0

    def draw(self, surface):
        draw_color = WHITE if self.flash_timer > 0 else self.color
        
        # 所有敌人都画成矩形（统一形状）
        pygame.draw.rect(surface, draw_color, self.rect)

        # 重装敌人绘制血条
        if self.type == ENEMY_HEAVY and self.max_hp > 1:
            bar_w = self.width
            bar_h = 4
            bar_x = self.x
            bar_y = self.y - 8
            pygame.draw.rect(surface, BLACK, (bar_x, bar_y, bar_w, bar_h))
            hp_ratio = self.hp / self.max_hp
            if hp_ratio > 0.5:
                bar_col = GREEN
            elif hp_ratio > 0.25:
                bar_col = YELLOW
            else:
                bar_col = RED
            pygame.draw.rect(surface, bar_col, (bar_x, bar_y, bar_w * hp_ratio, bar_h))

    def off_screen(self):
        if self.type == ENEMY_NORMAL or self.type == ENEMY_HEAVY:
            return self.y > HEIGHT
        else:
            return (self.y > HEIGHT or
                    self.x < -self.width or
                    self.x > WIDTH + self.width)