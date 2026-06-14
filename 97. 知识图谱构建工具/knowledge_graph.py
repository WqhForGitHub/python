"""
知识图谱构建工具 - 纯 Python 实现
=====================================
功能：
- 实体 / 关系 / 三元组 (subject, predicate, object) 数据模型
- 从文本中通过简单规则抽取三元组
- 知识图谱存储（内存 + JSON 持久化）
- 查询：按主语 / 宾语 / 谓词 / 一跳邻居 / N 跳路径
- ASCII 可视化（邻接表格式）
"""

import json
import os
import re
from collections import defaultdict, deque


class KnowledgeGraph:
    def __init__(self):
        self.entities = set()
        self.triples = []                       # [(s, p, o)]
        self.spo = defaultdict(list)            # s -> [(p, o)]
        self.ops = defaultdict(list)            # o -> [(p, s)]
        self.predicates = defaultdict(list)     # p -> [(s, o)]

    # ---------- 增删 ----------
    def add(self, s, p, o):
        triple = (s, p, o)
        if triple in self.triples:
            return
        self.triples.append(triple)
        self.entities.add(s)
        self.entities.add(o)
        self.spo[s].append((p, o))
        self.ops[o].append((p, s))
        self.predicates[p].append((s, o))

    def remove(self, s, p, o):
        triple = (s, p, o)
        if triple not in self.triples:
            return False
        self.triples.remove(triple)
        self.spo[s].remove((p, o))
        self.ops[o].remove((p, s))
        self.predicates[p].remove((s, o))
        return True

    # ---------- 查询 ----------
    def query(self, s=None, p=None, o=None):
        """三元组模式匹配，None 表示通配"""
        results = []
        for t in self.triples:
            if (s is None or t[0] == s) and (p is None or t[1] == p) and (o is None or t[2] == o):
                results.append(t)
        return results

    def neighbors(self, entity, depth=1):
        """BFS 找 N 跳邻居"""
        visited = {entity: 0}
        q = deque([entity])
        while q:
            cur = q.popleft()
            d = visited[cur]
            if d >= depth:
                continue
            for p, o in self.spo.get(cur, []):
                if o not in visited:
                    visited[o] = d + 1
                    q.append(o)
            for p, s in self.ops.get(cur, []):
                if s not in visited:
                    visited[s] = d + 1
                    q.append(s)
        del visited[entity]
        return visited  # entity -> distance

    def find_path(self, src, dst, max_depth=5):
        """BFS 找最短路径"""
        if src == dst:
            return [src]
        visited = {src: None}
        q = deque([(src, 0)])
        while q:
            cur, d = q.popleft()
            if d >= max_depth:
                continue
            adj = [(o, p, "->") for p, o in self.spo.get(cur, [])]
            adj += [(s, p, "<-") for p, s in self.ops.get(cur, [])]
            for nxt, p, dir_ in adj:
                if nxt in visited:
                    continue
                visited[nxt] = (cur, p, dir_)
                if nxt == dst:
                    # 回溯
                    path = []
                    node = dst
                    while node is not None:
                        prev = visited[node]
                        if prev is None:
                            path.append(node)
                            break
                        path.append((node, prev[1], prev[2]))
                        node = prev[0]
                    path.reverse()
                    return path
                q.append((nxt, d + 1))
        return None

    # ---------- 持久化 ----------
    def save(self, path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"triples": self.triples}, f, ensure_ascii=False, indent=2)

    def load(self, path):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        for s, p, o in data["triples"]:
            self.add(s, p, o)

    # ---------- 可视化 ----------
    def show(self):
        for ent in sorted(self.entities):
            outs = self.spo.get(ent, [])
            if not outs:
                continue
            print(f"  {ent}")
            for p, o in outs:
                print(f"    --[{p}]--> {o}")


# ---------- 简单规则抽取器 ----------
class SimpleExtractor:
    """基于模式匹配的轻量级三元组抽取器"""

    PATTERNS = [
        # 中文模式
        (r"(\S+?)\s*是\s*(\S+?)的\s*(\S+)", lambda m: (m.group(1), m.group(3) + "_of", m.group(2))),
        (r"(\S+?)\s*是\s*(\S+)", lambda m: (m.group(1), "is_a", m.group(2))),
        (r"(\S+?)\s*位于\s*(\S+)", lambda m: (m.group(1), "located_in", m.group(2))),
        (r"(\S+?)\s*创立于\s*(\S+)", lambda m: (m.group(1), "founded_in", m.group(2))),
        (r"(\S+?)\s*创立了\s*(\S+)", lambda m: (m.group(1), "founder_of", m.group(2))),
        (r"(\S+?)\s*出生于\s*(\S+)", lambda m: (m.group(1), "born_in", m.group(2))),
        (r"(\S+?)\s*工作于\s*(\S+)", lambda m: (m.group(1), "works_at", m.group(2))),
        # 英文
        (r"(\w+)\s+is\s+a\s+(\w+)", lambda m: (m.group(1), "is_a", m.group(2))),
        (r"(\w+)\s+founded\s+(\w+)", lambda m: (m.group(1), "founder_of", m.group(2))),
    ]

    @classmethod
    def extract(cls, text):
        results = []
        # 按句子切分
        sentences = re.split(r"[。.!?！？\n]", text)
        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue
            for pat, fn in cls.PATTERNS:
                for m in re.finditer(pat, sent):
                    results.append(fn(m))
        return results


def demo():
    kg = KnowledgeGraph()

    # 手动添加
    facts = [
        ("北京", "is_a", "城市"),
        ("北京", "capital_of", "中国"),
        ("中国", "is_a", "国家"),
        ("清华大学", "located_in", "北京"),
        ("张三", "works_at", "清华大学"),
        ("张三", "born_in", "上海"),
        ("上海", "is_a", "城市"),
        ("李四", "is_a", "学生"),
        ("李四", "studies_at", "清华大学"),
    ]
    for s, p, o in facts:
        kg.add(s, p, o)

    # 文本抽取
    text = """
    马云创立了阿里巴巴。
    阿里巴巴是一个公司。
    马云出生于杭州。
    杭州位于浙江。
    """
    extracted = SimpleExtractor.extract(text)
    print("=" * 50)
    print("从文本抽取的三元组：")
    for t in extracted:
        print(f"  {t}")
        kg.add(*t)

    print("\n=" * 25)
    print("\n图谱结构：")
    kg.show()

    print("\n--- 查询：北京的所有关系 ---")
    for t in kg.query(s="北京"):
        print(f"  {t}")
    for t in kg.query(o="北京"):
        print(f"  (反向) {t}")

    print("\n--- 张三 的 2 跳邻居 ---")
    for ent, dist in sorted(kg.neighbors("张三", depth=2).items(), key=lambda x: x[1]):
        print(f"  {ent} (距离={dist})")

    print("\n--- 路径：李四 -> 中国 ---")
    path = kg.find_path("李四", "中国", max_depth=4)
    if path:
        print(f"  起点: {path[0]}")
        for step in path[1:]:
            node, pred, dir_ = step
            arrow = f"--[{pred}]-->" if dir_ == "->" else f"<--[{pred}]--"
            print(f"    {arrow} {node}")
    else:
        print("  (未找到路径)")

    # 持久化
    out = "kg_demo.json"
    kg.save(out)
    print(f"\n已保存到 {out}")
    if os.path.exists(out):
        size = os.path.getsize(out)
        print(f"  文件大小: {size} bytes")
        os.remove(out)
        print("(演示完毕，文件已清理)")
    print("=" * 50)


if __name__ == "__main__":
    demo()
