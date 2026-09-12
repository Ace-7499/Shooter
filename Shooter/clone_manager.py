import math
from effects import Explosion
from settings import ENEMY_SCORE_BASE   # 导入基础分数

def update_clones(clones, enemies, double_score_timer, explosions, rapid_timer=0):
    """
    更新克隆，传入 rapid_timer 以让分身享受射速加成
    返回本次击杀获得的分数（score_gain）
    """
    score_gain = 0

    # 1. 分身自身更新（包括自爆）
    for c in clones[:]:
        alive = c.update(enemies, rapid_timer)
        if not alive:
            if c.exploded:
                # 自爆范围伤害
                cx = c.x + c.width//2
                cy = c.y + c.height//2
                explosions.append(Explosion(cx, cy, 50))
                for e in enemies[:]:
                    dist = math.hypot(e.x + e.width//2 - cx, e.y + e.height//2 - cy)
                    if dist <= c.explode_radius:
                        explosions.append(Explosion(e.x + e.width//2, e.y + e.height//2, 20))
                        enemies.remove(e)
                        # 自爆击杀加分（一击必杀）
                        score_gain += ENEMY_SCORE_BASE * 2 if double_score_timer > 0 else ENEMY_SCORE_BASE
            clones.remove(c)

    # 2. 克隆子弹碰撞（一击必杀）
    for c in clones:
        for b in c.bullets[:]:
            if b not in c.bullets:
                continue
            hit = False
            for test_rect in b.get_path_rects():
                for e in enemies[:]:
                    if test_rect.colliderect(e.rect):
                        explosions.append(Explosion(e.x + e.width//2, e.y + e.height//2))
                        enemies.remove(e)
                        # 子弹击杀加分
                        score_gain += ENEMY_SCORE_BASE * 2 if double_score_timer > 0 else ENEMY_SCORE_BASE
                        if b in c.bullets:
                            c.bullets.remove(b)
                        hit = True
                        break
                if hit:
                    break

    # 3. 分身挡伤害（敌人撞到分身，分身和敌人同归于尽）
    for c in clones[:]:
        for e in enemies[:]:
            if c.collide_with_enemy(e):
                explosions.append(Explosion(e.x + e.width//2, e.y + e.height//2))
                enemies.remove(e)
                # 挡伤害击杀加分（是否加分取决于设计，这里也加）
                score_gain += ENEMY_SCORE_BASE * 2 if double_score_timer > 0 else ENEMY_SCORE_BASE
                if c.hp <= 0:
                    clones.remove(c)
                break

    return score_gain