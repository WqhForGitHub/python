"""
2D 游戏引擎（简化版）- 纯 Python 实现
=====================================
仅依赖标准库，提供：
- 实体组件系统 (ECS)
- 向量数学 (Vec2)
- 物理模拟（位置、速度、重力）
- AABB 碰撞检测
- 输入事件分发
- 主循环（固定时间步长）
- 终端 ASCII 渲染器（可替换）
- 场景管理
"""

import time
import math
import os
import sys


# ---------- 向量 ----------
class Vec2:
    __slots__ = ("x", "y")

    def __init__(self, x=0.0, y=0.0):
        self.x = float(x)
        self.y = float(y)

    def __add__(self, o): return Vec2(self.x + o.x, self.y + o.y)
    def __sub__(self, o): return Vec2(self.x - o.x, self.y - o.y)
    def __mul__(self, s): return Vec2(self.x * s, self.y * s)
    def __repr__(self): return f"Vec2({self.x:.2f}, {self.y:.2f})"

    def length(self): return math.sqrt(self.x * self.x + self.y * self.y)


# ---------- 组件 ----------
class Component:
    pass


class Transform(Component):
    def __init__(self, x=0, y=0):
        self.pos = Vec2(x, y)


class RigidBody(Component):
    def __init__(self, vx=0, vy=0, gravity=0.0, friction=0.0):
        self.vel = Vec2(vx, vy)
        self.gravity = gravity
        self.friction = friction


class BoxCollider(Component):
    def __init__(self, w=1, h=1, on_collide=None):
        self.w = w
        self.h = h
        self.on_collide = on_collide  # callback(self_entity, other_entity)


class Sprite(Component):
    def __init__(self, char="#"):
        self.char = char


class Tag(Component):
    def __init__(self, name):
        self.name = name


# ---------- 实体 ----------
class Entity:
    _next_id = 0

    def __init__(self):
        Entity._next_id += 1
        self.id = Entity._next_id
        self.alive = True
        self.components = {}

    def add(self, comp):
        self.components[type(comp)] = comp
        return self

    def get(self, cls):
        return self.components.get(cls)

    def has(self, *classes):
        return all(c in self.components for c in classes)


# ---------- 系统 ----------
class System:
    def update(self, world, dt): pass


class PhysicsSystem(System):
    def update(self, world, dt):
        for e in world.entities:
            if e.has(Transform, RigidBody):
                t = e.get(Transform)
                r = e.get(RigidBody)
                r.vel.y += r.gravity * dt
                r.vel = r.vel * (1 - r.friction * dt)
                t.pos = t.pos + r.vel * dt


class CollisionSystem(System):
    @staticmethod
    def aabb(t1, c1, t2, c2):
        return (t1.pos.x < t2.pos.x + c2.w and
                t1.pos.x + c1.w > t2.pos.x and
                t1.pos.y < t2.pos.y + c2.h and
                t1.pos.y + c1.h > t2.pos.y)

    def update(self, world, dt):
        ents = [e for e in world.entities if e.has(Transform, BoxCollider)]
        for i in range(len(ents)):
            for j in range(i + 1, len(ents)):
                a, b = ents[i], ents[j]
                if self.aabb(a.get(Transform), a.get(BoxCollider),
                             b.get(Transform), b.get(BoxCollider)):
                    ca, cb = a.get(BoxCollider), b.get(BoxCollider)
                    if ca.on_collide:
                        ca.on_collide(a, b)
                    if cb.on_collide:
                        cb.on_collide(b, a)


class AsciiRenderer(System):
    def __init__(self, width=40, height=15):
        self.w = width
        self.h = height

    def update(self, world, dt):
        grid = [[" "] * self.w for _ in range(self.h)]
        for e in world.entities:
            if e.has(Transform, Sprite):
                t = e.get(Transform)
                sp = e.get(Sprite)
                x, y = int(t.pos.x), int(t.pos.y)
                if 0 <= x < self.w and 0 <= y < self.h:
                    grid[y][x] = sp.char
        # 清屏
        sys.stdout.write("\033[H\033[J")
        sys.stdout.write("+" + "-" * self.w + "+\n")
        for row in grid:
            sys.stdout.write("|" + "".join(row) + "|\n")
        sys.stdout.write("+" + "-" * self.w + "+\n")
        sys.stdout.flush()


# ---------- 世界 / 引擎 ----------
class World:
    def __init__(self):
        self.entities = []
        self.systems = []
        self.events = []  # 待处理事件

    def add_entity(self, e):
        self.entities.append(e)
        return e

    def add_system(self, s):
        self.systems.append(s)
        return s

    def emit(self, event):
        self.events.append(event)

    def update(self, dt):
        for s in self.systems:
            s.update(self, dt)
        # 清理死亡实体
        self.entities = [e for e in self.entities if e.alive]


class Engine:
    def __init__(self, world, target_fps=20, max_steps=None):
        self.world = world
        self.target_fps = target_fps
        self.dt = 1.0 / target_fps
        self.running = False
        self.max_steps = max_steps
        self.steps = 0

    def run(self):
        self.running = True
        last = time.time()
        while self.running:
            now = time.time()
            elapsed = now - last
            if elapsed < self.dt:
                time.sleep(self.dt - elapsed)
            last = time.time()
            self.world.update(self.dt)
            self.steps += 1
            if self.max_steps is not None and self.steps >= self.max_steps:
                self.running = False


# ---------- Demo: 弹球 ----------
def demo():
    print("初始化 2D 游戏引擎演示...")
    print("场景：一个小球从顶部落下，在地面弹跳；遇到墙壁时会变向。")
    print("(渲染模式：终端 ASCII，按 Ctrl+C 退出)\n")
    time.sleep(1)

    world = World()

    # 球
    ball = Entity()
    ball.add(Transform(20, 2))
    ball.add(RigidBody(vx=8, vy=0, gravity=20, friction=0.0))
    ball.add(BoxCollider(1, 1))
    ball.add(Sprite("●"))
    ball.add(Tag("ball"))
    world.add_entity(ball)

    # 地面 / 墙壁（视觉装饰，碰撞由系统逻辑处理）
    # 这里我们手动在物理后做边界反弹
    class BoundarySystem(System):
        def __init__(self, w, h):
            self.w = w
            self.h = h

        def update(self, world, dt):
            for e in world.entities:
                if e.has(Transform, RigidBody):
                    t = e.get(Transform)
                    r = e.get(RigidBody)
                    if t.pos.x < 0:
                        t.pos.x = 0
                        r.vel.x = abs(r.vel.x)
                    elif t.pos.x > self.w - 1:
                        t.pos.x = self.w - 1
                        r.vel.x = -abs(r.vel.x)
                    if t.pos.y > self.h - 1:
                        t.pos.y = self.h - 1
                        r.vel.y = -abs(r.vel.y) * 0.85  # 弹性损失
                    elif t.pos.y < 0:
                        t.pos.y = 0
                        r.vel.y = abs(r.vel.y)

    width, height = 40, 15
    world.add_system(PhysicsSystem())
    world.add_system(BoundarySystem(width, height))
    world.add_system(CollisionSystem())
    world.add_system(AsciiRenderer(width, height))

    engine = Engine(world, target_fps=15, max_steps=60)
    try:
        engine.run()
    except KeyboardInterrupt:
        pass
    print("\n演示结束。引擎共运行了 {} 帧。".format(engine.steps))


if __name__ == "__main__":
    demo()
