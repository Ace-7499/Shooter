import pygame
import random
import math
from settings import *

# ---------- 爆炸粒子 ----------
class Particle:
    def __init__(self, x, y, color=None, size_range=(4, 10)):
        self.x = x
        self.y = y
        self.size = random.randint(*size_range)
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 5)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = random.randint(20, 40)
        self.color = color if color else random.choice([RED, ORANGE, YELLOW])

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        self.size *= 0.98

    def draw(self, surface):
        if self.life > 0:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(self.size))

    def alive(self):
        return self.life > 0


# ---------- 爆炸管理（支持自定义粒子数量） ----------
class Explosion:
    def __init__(self, x, y, particle_count=15):
        self.particles = [Particle(x, y) for _ in range(particle_count)]

    def update(self):
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.alive()]

    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)

    def finished(self):
        return len(self.particles) == 0


# ---------- 冲击波特效 ----------
class Shockwave:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 25
        self.max_radius = SHOCKWAVE_RADIUS
        self.speed = 10
        self.life = True

    def update(self):
        self.radius += self.speed
        if self.radius >= self.max_radius:
            self.life = False

    def draw(self, surface):
        if self.life:
            alpha = max(0, int(255 * (1 - self.radius / self.max_radius)))
            color = (200, 200, 200) if alpha > 100 else (100, 100, 100)
            pygame.draw.circle(surface, color, (int(self.x), int(self.y)), int(self.radius), 3)


# ---------- 追踪导弹（支持指定出生位置） ----------
class Missile:
    def __init__(self, x=None, y=None):
        self.width = 26
        self.height = 10
        if x is None:
            if random.random() < 0.5:
                self.x = -self.width
                self.vx = 9
            else:
                self.x = WIDTH
                self.vx = -9
            self.y = random.randint(60, HEIGHT - 100)
            self.angle = math.atan2(0, self.vx)
        else:
            self.x = x
            self.y = y
            self.vx = 0
            self.angle = -math.pi / 2
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.speed = 10
        self.turn_rate = 0.175
        self.target = None
        self.trail = []

    def move(self, enemies):
        if self.target is None or self.target not in enemies:
            nearest = None
            min_dist = float('inf')
            for e in enemies:
                dist = math.hypot(e.x + e.width//2 - self.x, e.y + e.height//2 - self.y)
                if dist < min_dist:
                    min_dist = dist
                    nearest = e
            self.target = nearest

        if self.target is not None:
            tx = self.target.x + self.target.width // 2
            ty = self.target.y + self.target.height // 2
            desired_angle = math.atan2(ty - self.y, tx - self.x)
            angle_diff = (desired_angle - self.angle + math.pi) % (2 * math.pi) - math.pi
            self.angle += angle_diff * self.turn_rate
        else:
            if self.vx != 0:
                self.angle = math.atan2(0.5, self.vx)
            else:
                self.angle = -math.pi / 2

        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        self.rect.x = self.x
        self.rect.y = self.y

        if random.random() < 0.6:
            self.trail.append(Particle(
                self.x + self.width//2,
                self.y + self.height//2,
                color=random.choice([(255, 215, 0), ORANGE, YELLOW]),
                size_range=(2, 5)
            ))
        for p in self.trail:
            p.update()
        self.trail = [p for p in self.trail if p.alive()]

    def draw(self, surface):
        for p in self.trail:
            p.draw(surface)
        tip = (self.x + math.cos(self.angle) * self.width,
               self.y + math.sin(self.angle) * self.width)
        left = (self.x + math.cos(self.angle + 2.5) * self.height,
                self.y + math.sin(self.angle + 2.5) * self.height)
        right = (self.x + math.cos(self.angle - 2.5) * self.height,
                 self.y + math.sin(self.angle - 2.5) * self.height)
        pygame.draw.polygon(surface, (255, 215, 0), [tip, left, right])
        flame_x = self.x - math.cos(self.angle) * 8
        flame_y = self.y - math.sin(self.angle) * 8
        pygame.draw.circle(surface, ORANGE, (int(flame_x), int(flame_y)), 5)

    def off_screen(self):
        margin = 100
        return (self.x < -margin or self.x > WIDTH + margin or
                self.y < -margin or self.y > HEIGHT + margin)


# ---------- 追踪穿透子弹（方形、红色、优化转向） ----------
class PenetratingBullet:
    def __init__(self, x, y):
        self.width = 35
        self.height = 15
        self.x = x
        self.y = y
        self.speed = PENETRATING_BULLET_SPEED
        self.turn_rate = 0.40           # 比例转向
        self.max_turn = 0.30            # 每帧最大转向角（防绕圈）
        self.pierce_count = MAX_PIERCE
        self.target = None
        self.trail = []
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

        # 初始角度设为向上，但在第一次 move 时会被修正
        self.angle = -math.pi / 2
        self.initialized = False

    def move(self, enemies):
        # 首次运行时锁定最近敌人并设定初始角度
        if not self.initialized:
            nearest = None
            min_dist = float('inf')
            for e in enemies:
                dist = math.hypot(e.x + e.width//2 - self.x, e.y + e.height//2 - self.y)
                if dist < min_dist:
                    min_dist = dist
                    nearest = e
            self.target = nearest
            if self.target is not None:
                dx = self.target.x + self.target.width//2 - self.x
                dy = self.target.y + self.target.height//2 - self.y
                if math.hypot(dx, dy) > 0:
                    self.angle = math.atan2(dy, dx)
            self.initialized = True

        # 如果目标丢失或死亡，重新锁定
        if self.target is None or self.target not in enemies:
            nearest = None
            min_dist = float('inf')
            for e in enemies:
                dist = math.hypot(e.x + e.width//2 - self.x, e.y + e.height//2 - self.y)
                if dist < min_dist:
                    min_dist = dist
                    nearest = e
            self.target = nearest

        # 追踪目标
        if self.target is not None:
            tx = self.target.x + self.target.width // 2
            ty = self.target.y + self.target.height // 2
            dx = tx - self.x
            dy = ty - self.y
            dist = math.hypot(dx, dy)
            if dist > 0:
                desired_angle = math.atan2(dy, dx)
                angle_diff = (desired_angle - self.angle + math.pi) % (2 * math.pi) - math.pi
                # 比例转向 + 限制最大转向角
                angle_diff *= self.turn_rate
                if abs(angle_diff) > self.max_turn:
                    angle_diff = self.max_turn if angle_diff > 0 else -self.max_turn
                self.angle += angle_diff

        # 移动
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        self.rect.x = self.x
        self.rect.y = self.y

        # 拖尾粒子
        if random.random() < 0.5:
            self.trail.append(Particle(
                self.x + self.width//2,
                self.y + self.height//2,
                color=random.choice([(255, 215, 0), ORANGE, YELLOW]),
                size_range=(2, 4)
            ))
        for p in self.trail:
            p.update()
        self.trail = [p for p in self.trail if p.alive()]

    def draw(self, surface):
        # 拖尾粒子（保持不变）
        for p in self.trail:
            p.draw(surface)
        
        # 绘制箭头（参考 Missile 的绘制，但没有白边和文字）
        tip = (self.x + math.cos(self.angle) * self.width,
               self.y + math.sin(self.angle) * self.width)
        left = (self.x + math.cos(self.angle + 2.8) * self.height,
                self.y + math.sin(self.angle + 2.8) * self.height)
        right = (self.x + math.cos(self.angle - 2.8) * self.height,
                 self.y + math.sin(self.angle - 2.8) * self.height)
        pygame.draw.polygon(surface, (255, 0, 0), [tip, left, right])
        pygame.draw.polygon(surface, ORANGE, [tip, left, right], 2)  # 添加橙色边框

    def off_screen(self):
        margin = 100
        return (self.x < -margin or self.x > WIDTH + margin or
                self.y < -margin or self.y > HEIGHT + margin)