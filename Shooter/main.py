import pygame
import random
import math
from settings import *
from player import Player
from bullet import Bullet
from enemy import Enemy
from powerup import PowerUp
from effects import Explosion, Shockwave, Missile, PenetratingBullet
from clone import Clone
from clone_manager import update_clones
from collision_manager import (
    handle_bullet_collisions,
    handle_missile_collisions,
    handle_penetrating_collisions,
    handle_player_collisions,
    handle_powerup_collisions
)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Shooter")
clock = pygame.time.Clock()

def draw_text(surface, text, size, x, y, color=WHITE):
    font = pygame.font.SysFont("Arial", size, bold=True)
    label = font.render(text, True, color)
    surface.blit(label, (x, y))

def main():
    running = True
    game_over = False
    score = 0
    next_missile_score = MISSILE_MILESTONE_STEP
    next_pierce_score = PIERCE_MILESTONE_STEP
    missile_milestone_count = 0
    next_clone_score = CLONE_SCORE_INTERVAL

    player = Player()
    bullets = []
    enemies = []
    powerups = []
    explosions = []
    shockwaves = []
    missiles = []
    penetrating_bullets = []
    clones = []

    enemy_spawn_timer = 0
    enemy_spawn_delay = 40
    powerup_spawn_timer = 0
    powerup_spawn_delay = 150

    shoot_cooldown = 0
    shockwave_cooldown = 0
    rapid_timer = 0
    double_score_timer = 0

    while running:
        clock.tick(60)

        # ---------- 事件 ----------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if game_over and event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                game_over = False
                score = 0
                next_missile_score = MISSILE_MILESTONE_STEP
                next_pierce_score = PIERCE_MILESTONE_STEP
                missile_milestone_count = 0
                next_clone_score = CLONE_SCORE_INTERVAL
                player = Player()
                bullets.clear()
                enemies.clear()
                powerups.clear()
                explosions.clear()
                shockwaves.clear()
                missiles.clear()
                penetrating_bullets.clear()
                clones.clear()
                enemy_spawn_timer = 0
                powerup_spawn_timer = 0
                shoot_cooldown = 0
                shockwave_cooldown = 0
                rapid_timer = 0
                double_score_timer = 0

        # ---------- 按键控制 ----------
        keys = pygame.key.get_pressed()
        if not game_over:
            dx = 0
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                dx = -player.speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                dx = player.speed
            player.move(dx)

            current_delay = RAPID_FIRE_DELAY if rapid_timer > 0 else SHOOT_DELAY
            if (keys[pygame.K_RETURN] or keys[pygame.K_SPACE]) and shoot_cooldown <= 0:
                bx = player.x + player.width // 2
                by = player.y
                bullets.append(Bullet(bx, by))
                shoot_cooldown = current_delay

            # 冲击波
            if (keys[pygame.K_v] or keys[pygame.K_b]) and shockwave_cooldown <= 0:
                cx = player.x + player.width // 2
                cy = player.y + player.height // 2
                shockwaves.append(Shockwave(cx, cy))
                for e in enemies[:]:
                    dist = math.hypot(e.x - cx, e.y - cy)
                    if dist <= SHOCKWAVE_RADIUS:
                        explosions.append(Explosion(e.x + e.width//2, e.y + e.height//2))
                        enemies.remove(e)
                        points = 2 * ENEMY_SCORE_BASE if double_score_timer > 0 else ENEMY_SCORE_BASE
                        score += points
                        # 冲击波杀死敌人也触发里程碑
                        while score >= next_missile_score:
                            missiles.append(Missile())
                            next_missile_score += MISSILE_MILESTONE_STEP
                            missile_milestone_count += 1
                            if missile_milestone_count >= 3:
                                powerups.append(PowerUp(force_type=POWERUP_MISSILE))
                                missile_milestone_count = 0
                        while score >= next_pierce_score:
                            penetrating_bullets.append(
                                PenetratingBullet(player.x + player.width//2, player.y)
                            )
                            next_pierce_score += PIERCE_MILESTONE_STEP
                shockwave_cooldown = SHOCKWAVE_COOLDOWN

        # 冷却递减
        if shoot_cooldown > 0:
            shoot_cooldown -= 1
        if shockwave_cooldown > 0:
            shockwave_cooldown -= 1

        # ---------- 游戏更新 ----------
        if not game_over:
            # 计时器
            if rapid_timer > 0:
                rapid_timer -= 1
            if double_score_timer > 0:
                double_score_timer -= 1

            # 子弹移动
            for b in bullets[:]:
                b.move()
                if b.off_screen():
                    bullets.remove(b)

            # 动态计算生成延迟：基础40帧，每1000分减2帧，最低10帧
            current_spawn_delay = max(10, 40 - (score // 1000) * 2)

            enemy_spawn_timer += 5
            if enemy_spawn_timer >= current_spawn_delay:
                enemy_type = random.choices(
                    [ENEMY_NORMAL, ENEMY_HOMING, ENEMY_DRUNK, ENEMY_TORNADO, ENEMY_HEAVY],
                    weights=[40, 10, 20, 10, 20]
                )[0]
                enemies.append(Enemy(enemy_type))
                enemy_spawn_timer = 0

            # 敌人移动
            ptx = player.x + player.width // 2
            pty = player.y + player.height // 2
            for e in enemies[:]:
                e.move(target_x=ptx, target_y=pty)
                if e.off_screen():
                    enemies.remove(e)

            # 道具生成和移动
            powerup_spawn_timer += 5
            if powerup_spawn_timer >= powerup_spawn_delay:
                powerups.append(PowerUp())
                powerup_spawn_timer = 0
            for p in powerups[:]:
                p.move()
                if p.off_screen():
                    powerups.remove(p)

            # 导弹移动
            for m in missiles[:]:
                m.move(enemies)
                if m.off_screen():
                    missiles.remove(m)

            # 穿透子弹移动
            for pb in penetrating_bullets[:]:
                pb.move(enemies)
                if pb.off_screen() or pb.pierce_count <= 0:
                    penetrating_bullets.remove(pb)

            # 克隆更新（含自爆、子弹碰撞、挡伤害）
            score += update_clones(clones, enemies, double_score_timer, explosions, rapid_timer)

            # ---------- 碰撞检测（统一调用管理器） ----------
            score += handle_bullet_collisions(bullets, enemies, double_score_timer, explosions)
            score += handle_missile_collisions(missiles, enemies, double_score_timer, explosions)
            score += handle_penetrating_collisions(penetrating_bullets, enemies, double_score_timer, explosions)

            if handle_player_collisions(player, enemies):
                game_over = True

            # 道具碰撞（玩家 + 分身）
            rapid_timer, double_score_timer = handle_powerup_collisions(
                player, powerups, rapid_timer, double_score_timer, missiles, clones
            )

            # ---------- 里程碑检查 ----------
            while score >= next_missile_score:
                missiles.append(Missile())
                next_missile_score += MISSILE_MILESTONE_STEP
                missile_milestone_count += 1
                if missile_milestone_count >= 3:
                    powerups.append(PowerUp(force_type=POWERUP_MISSILE))
                    missile_milestone_count = 0
            while score >= next_pierce_score:
                penetrating_bullets.append(
                    PenetratingBullet(player.x + player.width // 2, player.y)
                )
                next_pierce_score += PIERCE_MILESTONE_STEP

            # 克隆生成（交替前方和侧边）
            while score >= next_clone_score:
                if len(clones) % 2 == 0:
                    clones.append(Clone(player, 'front'))
                else:
                    clones.append(Clone(player, 'side'))
                next_clone_score += CLONE_SCORE_INTERVAL

            # 特效更新
            for sw in shockwaves:
                sw.update()
            shockwaves = [sw for sw in shockwaves if sw.life]
            for exp in explosions:
                exp.update()
            explosions = [exp for exp in explosions if not exp.finished()]

        # ---------- 绘制 ----------
        screen.fill(BLACK)
        for e in enemies:
            e.draw(screen)

        player_color = BLUE if rapid_timer > 0 else GREEN if double_score_timer > 0 else YELLOW
        player.draw(screen, player_color)

        for b in bullets:
            b.draw(screen)
        for p in powerups:
            p.draw(screen)
        for m in missiles:
            m.draw(screen)
        for pb in penetrating_bullets:
            pb.draw(screen)
        for c in clones:
            c.draw(screen)
        for sw in shockwaves:
            sw.draw(screen)
        for exp in explosions:
            exp.draw(screen)

        # UI
        draw_text(screen, f"Score: {score}", 24, 10, 10)
        draw_text(screen, f"Missile milestone: {missile_milestone_count}/3", 18, 10, 36, PURPLE)
        y_offset = 60
        if rapid_timer > 0:
            draw_text(screen, f"RAPID: {rapid_timer//60+1}s", 20, 10, y_offset, BLUE)
            y_offset += 25
        if double_score_timer > 0:
            draw_text(screen, f"DOUBLE: {double_score_timer//60+1}s", 20, 10, y_offset, GREEN)
            y_offset += 25
        if shockwave_cooldown > 0:
            draw_text(screen, f"SHOCKWAVE: {shockwave_cooldown//60+1}s", 20, 10, y_offset, CYAN)

        if game_over:
            draw_text(screen, "GAME OVER", 50, WIDTH//2-140, HEIGHT//2-40, RED)
            draw_text(screen, "Press R to Restart", 30, WIDTH//2-120, HEIGHT//2+20)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()