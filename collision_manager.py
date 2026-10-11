import math
from settings import *
from effects import Explosion, Missile
from powerup import PowerUp      # 如果需要，但此文件中未直接使用 PowerUp 类

def handle_bullet_collisions(bullets, enemies, double_score_timer, explosions):
    """普通子弹碰撞，返回所得分数"""
    score_gain = 0
    for b in bullets[:]:
        for e in enemies[:]:
            if b.rect.colliderect(e.rect):
                if b in bullets:
                    bullets.remove(b)
                dead = e.take_damage()
                if dead:
                    explosions.append(Explosion(e.x + e.width//2, e.y + e.height//2))
                    enemies.remove(e)
                    score_gain += 2 * ENEMY_SCORE_BASE if double_score_timer > 0 else ENEMY_SCORE_BASE
                break
    return score_gain

def handle_missile_collisions(missiles, enemies, double_score_timer, explosions):
    """追踪导弹碰撞，返回所得分数"""
    score_gain = 0
    for m in missiles[:]:
        for e in enemies[:]:
            if m.rect.colliderect(e.rect):
                if m in missiles:
                    missiles.remove(m)
                explosions.append(Explosion(e.x + e.width//2, e.y + e.height//2))
                enemies.remove(e)
                score_gain += 2 * ENEMY_SCORE_BASE if double_score_timer > 0 else ENEMY_SCORE_BASE
                break
    return score_gain

def handle_penetrating_collisions(penetrating_bullets, enemies, double_score_timer, explosions):
    """穿透子弹碰撞，返回所得分数"""
    score_gain = 0
    for pb in penetrating_bullets[:]:
        for e in enemies[:]:
            if pb.rect.colliderect(e.rect):
                dead = e.take_damage()
                if dead:
                    explosions.append(Explosion(e.x + e.width//2, e.y + e.height//2))
                    enemies.remove(e)
                    score_gain += 2 * ENEMY_SCORE_BASE if double_score_timer > 0 else ENEMY_SCORE_BASE
                pb.pierce_count -= 1
                if pb.pierce_count <= 0:
                    penetrating_bullets.remove(pb)
                    break
    return score_gain

def handle_player_collisions(player, enemies):
    """玩家与敌人碰撞，返回是否游戏结束"""
    for e in enemies:
        if player.rect.colliderect(e.rect):
            return True
    return False

def handle_powerup_collisions(player, powerups, rapid_timer, double_score_timer, missiles, clones):
    """处理玩家和分身的道具碰撞，返回更新后的定时器"""
    # ---- 玩家与道具碰撞 ----
    for p in powerups[:]:
        if player.rect.colliderect(p.rect):
            if p.type == POWERUP_RAPID:
                rapid_timer = EFFECT_DURATION
            elif p.type == POWERUP_DOUBLE:
                double_score_timer = EFFECT_DURATION
            elif p.type == POWERUP_MISSILE:
                for _ in range(5):
                    missiles.append(Missile())
            powerups.remove(p)

    # ---- 分身与道具碰撞 ----
    for c in clones[:]:
        for p in powerups[:]:
            if c.rect.colliderect(p.rect):
                if p.type == POWERUP_RAPID:
                    rapid_timer = EFFECT_DURATION
                elif p.type == POWERUP_DOUBLE:
                    double_score_timer = EFFECT_DURATION
                elif p.type == POWERUP_MISSILE:
                    for _ in range(5):
                        missiles.append(Missile())
                powerups.remove(p)
                break   # 每个分身只吃一个道具

    return rapid_timer, double_score_timer