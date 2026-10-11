import pygame
import math
import random
from settings import *

class Clone:
    def __init__(self, target_player, position='side'):
        self.width = 36
        self.height = 36
        self.player = target_player
        self.position = position

        if position == 'side':
            self.x = random.randint(50, WIDTH - 50)
            self.offset_x = random.choice([-55, 55])
            self.offset_y = -15
        else:  # front
            self.x = target_player.x + target_player.width//2 - self.width//2
            self.offset_x = 0
            self.offset_y = -60

        self.y = HEIGHT + 30
        self.speed = 3.5
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

        self.target = None
        self.aim_timer = 0
        self.aim_delay = 30
        self.attack_cooldown = 0
        self.attack_interval = 12        # 基础攻击间隔（帧）
        self.hp = 1

        self.state = 'approaching'      # 'approaching', 'following', 'exploding'

        self.bullets = []
        self.color = (255, 200, 50)     # 橙黄色，与玩家相近
        self.bullet_speed = 18

        # 自爆属性
        self.lifetime = 600
        self.timer = 0
        self.exploded = False
        self.explode_radius = 200

        # 固定朝向：始终朝上（正常状态）
        self.heading = -math.pi / 2

    def update(self, enemies, rapid_timer=0):
        """传入 rapid_timer 以判断是否享受射速加成"""
        if self.hp <= 0:
            return False

        # 计算当前攻击间隔（射速加成时缩短）
        current_interval = self.attack_interval
        if rapid_timer > 0:
            current_interval = 3   # 加速后每4帧射一发

        # 计时器增加
        self.timer += 1
        if self.timer >= self.lifetime and self.state != 'exploding':
            self.state = 'exploding'
            self.speed = 8.0
            # 锁定最近的敌人
            nearest = None
            min_dist = float('inf')
            for e in enemies:
                dist = math.hypot(e.x + e.width//2 - (self.x + self.width//2),
                                  e.y + e.height//2 - (self.y + self.height//2))
                if dist < min_dist:
                    min_dist = dist
                    nearest = e
            self.target = nearest
            if self.target is None:
                return False

        # ---- 移动逻辑 ----
        if self.state == 'approaching':
            target_x = self.player.x + self.player.width//2 + self.offset_x - self.width//2
            target_y = self.player.y + self.player.height//2 + self.offset_y - self.height//2
            target_x = max(0, min(WIDTH - self.width, target_x))
            target_y = max(0, min(HEIGHT - self.height, target_y))
            dx = target_x - self.x
            dy = target_y - self.y
            dist = math.hypot(dx, dy)
            if dist > 5:
                if dist != 0:
                    dx /= dist
                    dy /= dist
                self.x += dx * self.speed
                self.y += dy * self.speed
            else:
                self.state = 'following'

        elif self.state == 'following':
            target_x = self.player.x + self.player.width//2 + self.offset_x - self.width//2
            target_y = self.player.y + self.player.height//2 + self.offset_y - self.height//2
            target_x = max(0, min(WIDTH - self.width, target_x))
            target_y = max(0, min(HEIGHT - self.height, target_y))
            self.x += (target_x - self.x) * 0.1
            self.y += (target_y - self.y) * 0.1

        else:  # exploding
            if self.target is not None and self.target in enemies:
                tx = self.target.x + self.target.width//2
                ty = self.target.y + self.target.height//2
                dx = tx - self.x
                dy = ty - self.y
                dist = math.hypot(dx, dy)
                if dist > 5:
                    if dist != 0:
                        dx /= dist
                        dy /= dist
                    self.x += dx * self.speed
                    self.y += dy * self.speed
                    self.heading = math.atan2(dy, dx)
                else:
                    self.exploded = True
                    return False
            else:
                nearest = None
                min_dist = float('inf')
                for e in enemies:
                    dist = math.hypot(e.x + e.width//2 - (self.x + self.width//2),
                                      e.y + e.height//2 - (self.y + self.height//2))
                    if dist < min_dist:
                        min_dist = dist
                        nearest = e
                self.target = nearest
                if self.target is None:
                    return False

        self.rect.x = self.x
        self.rect.y = self.y

        # ---- 攻击（仅在非自爆状态） ----
        if self.state != 'exploding':
            if self.attack_cooldown > 0:
                self.attack_cooldown -= 1

            nearest = None
            min_dist = float('inf')
            for e in enemies:
                dist = math.hypot(e.x + e.width//2 - (self.x + self.width//2),
                                  e.y + e.height//2 - (self.y + self.height//2))
                if dist < min_dist:
                    min_dist = dist
                    nearest = e
            self.target = nearest

            if self.target is not None and self.target in enemies:
                self.aim_timer += 1
                if self.aim_timer >= self.aim_delay and self.attack_cooldown <= 0:
                    bullet = CloneBullet(self.x + self.width//2, self.y + self.height//2,
                                         self.target, self.bullet_speed)
                    self.bullets.append(bullet)
                    self.aim_timer = 0
                    self.attack_cooldown = current_interval   # 使用动态间隔
            else:
                self.aim_timer = 0

        # ---- 子弹更新（无论什么状态都执行） ----
        for b in self.bullets[:]:
            b.update(enemies)
            if b.off_screen():
                self.bullets.remove(b)

        return True

    def draw(self, surface):
        # 颜色
        if self.state == 'exploding':
            draw_color = (255, 0, 0) if (self.timer // 3) % 2 == 0 else (255, 200, 200)
        else:
            draw_color = self.color

        # 旋转三角形
        cx = self.x + self.width // 2
        cy = self.y + self.height // 2
        tip_offset = (self.width // 2, 0)
        left_offset = (-self.width // 2, -self.height // 2)
        right_offset = (-self.width // 2, self.height // 2)

        cos_a = math.cos(self.heading)
        sin_a = math.sin(self.heading)
        tip_x = cx + tip_offset[0] * cos_a - tip_offset[1] * sin_a
        tip_y = cy + tip_offset[0] * sin_a + tip_offset[1] * cos_a
        left_x = cx + left_offset[0] * cos_a - left_offset[1] * sin_a
        left_y = cy + left_offset[0] * sin_a + left_offset[1] * cos_a
        right_x = cx + right_offset[0] * cos_a - right_offset[1] * sin_a
        right_y = cy + right_offset[0] * sin_a + right_offset[1] * cos_a

        points = [(tip_x, tip_y), (left_x, left_y), (right_x, right_y)]
        pygame.draw.polygon(surface, draw_color, points)
        pygame.draw.polygon(surface, WHITE, points, 2)

        # 瞄准标志
        if self.state != 'exploding' and self.target is not None and self.aim_timer > 0:
            cx_target = self.target.x + self.target.width // 2
            cy_target = self.target.y + self.target.height // 2
            progress = self.aim_timer / self.aim_delay
            radius = 40 - (40 - 10) * progress
            pulse = math.sin(progress * math.pi * 2) * 0.5 + 0.5
            brightness = int(100 + 155 * pulse)
            color = (brightness, 0, 0)
            pygame.draw.circle(surface, color, (int(cx_target), int(cy_target)), int(radius), 3)
            length = int(radius * 0.6)
            pygame.draw.line(surface, color, (cx_target - length, cy_target), (cx_target + length, cy_target), 2)
            pygame.draw.line(surface, color, (cx_target, cy_target - length), (cx_target, cy_target + length), 2)

        # 子弹
        for b in self.bullets:
            b.draw(surface)

    def collide_with_enemy(self, enemy):
        if self.state == 'exploding':
            return False
        if self.rect.colliderect(enemy.rect):
            self.hp -= 1
            return True
        return False


# ---------- 子弹类 ----------
class CloneBullet:
    def __init__(self, x, y, target, speed):
        self.x = x
        self.y = y
        self.last_x = x
        self.last_y = y
        self.target = target
        self.speed = speed
        self.size = 15
        self.draw_size = 20
        self.turn_rate = 0.20
        self.max_turn = 0.30
        self.alive = True
        self.rect = pygame.Rect(x - self.size//2, y - self.size//2, self.size, self.size)

        if target is not None:
            dx = target.x + target.width//2 - x
            dy = target.y + target.height//2 - y
            self.angle = math.atan2(dy, dx)
        else:
            self.angle = 0

    def update(self, enemies):
        if not self.alive:
            return

        if self.target not in enemies:
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
            dx = tx - self.x
            dy = ty - self.y
            dist = math.hypot(dx, dy)
            if dist > 0:
                desired_angle = math.atan2(dy, dx)
                angle_diff = (desired_angle - self.angle + math.pi) % (2 * math.pi) - math.pi
                angle_diff *= self.turn_rate
                if abs(angle_diff) > self.max_turn:
                    angle_diff = self.max_turn if angle_diff > 0 else -self.max_turn
                self.angle += angle_diff

        self.last_x = self.x
        self.last_y = self.y

        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        self.rect.x = self.x - self.size//2
        self.rect.y = self.y - self.size//2

    def draw(self, surface):
        if not self.alive:
            return
        tip = (self.x + math.cos(self.angle) * self.draw_size,
               self.y + math.sin(self.angle) * self.draw_size)
        left = (self.x + math.cos(self.angle + 2.5) * (self.draw_size // 2),
                self.y + math.sin(self.angle + 2.5) * (self.draw_size // 2))
        right = (self.x + math.cos(self.angle - 2.5) * (self.draw_size // 2),
                 self.y + math.sin(self.angle - 2.5) * (self.draw_size // 2))
        pygame.draw.polygon(surface, (0, 200, 255), [tip, left, right])
        pygame.draw.polygon(surface, WHITE, [tip, left, right], 1)

    def off_screen(self):
        margin = 50
        return (not self.alive or
                self.x < -margin or self.x > WIDTH + margin or
                self.y < -margin or self.y > HEIGHT + margin)

    def get_rect(self):
        return self.rect

    def get_path_rects(self):
        start = (self.last_x, self.last_y)
        end = (self.x, self.y)
        steps = 8
        for i in range(steps + 1):
            t = i / steps
            x = start[0] + (end[0] - start[0]) * t
            y = start[1] + (end[1] - start[1]) * t
            yield pygame.Rect(x - self.size//2, y - self.size//2, self.size, self.size)