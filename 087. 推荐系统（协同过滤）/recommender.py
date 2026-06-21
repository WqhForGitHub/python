"""
推荐系统（协同过滤）- 纯 Python 实现
=====================================
实现两种经典的协同过滤算法：
1. 基于用户的协同过滤 (User-Based CF)
2. 基于物品的协同过滤 (Item-Based CF)

相似度计算：余弦相似度、皮尔逊相关系数
评分预测：加权平均
"""

import math
from collections import defaultdict


class CollaborativeFiltering:
    def __init__(self):
        # 用户-物品评分矩阵: {user: {item: rating}}
        self.user_ratings = defaultdict(dict)
        # 物品-用户评分矩阵: {item: {user: rating}}
        self.item_ratings = defaultdict(dict)

    def add_rating(self, user, item, rating):
        """添加一条评分记录"""
        self.user_ratings[user][item] = rating
        self.item_ratings[item][user] = rating

    def load_data(self, data):
        """批量加载评分数据，data 是 (user, item, rating) 的列表"""
        for user, item, rating in data:
            self.add_rating(user, item, rating)

    # ---------- 相似度计算 ----------
    @staticmethod
    def cosine_similarity(vec_a, vec_b):
        """余弦相似度，vec_a / vec_b 是 dict"""
        common = set(vec_a) & set(vec_b)
        if not common:
            return 0.0
        dot = sum(vec_a[k] * vec_b[k] for k in common)
        norm_a = math.sqrt(sum(v * v for v in vec_a.values()))
        norm_b = math.sqrt(sum(v * v for v in vec_b.values()))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    @staticmethod
    def pearson_similarity(vec_a, vec_b):
        """皮尔逊相关系数"""
        common = list(set(vec_a) & set(vec_b))
        n = len(common)
        if n < 2:
            return 0.0
        mean_a = sum(vec_a[k] for k in common) / n
        mean_b = sum(vec_b[k] for k in common) / n
        num = sum((vec_a[k] - mean_a) * (vec_b[k] - mean_b) for k in common)
        den_a = math.sqrt(sum((vec_a[k] - mean_a) ** 2 for k in common))
        den_b = math.sqrt(sum((vec_b[k] - mean_b) ** 2 for k in common))
        if den_a == 0 or den_b == 0:
            return 0.0
        return num / (den_a * den_b)

    # ---------- 基于用户的 CF ----------
    def user_based_recommend(self, user, top_n=5, k_neighbors=10, sim_func=None):
        """为指定用户推荐 top_n 个未交互物品"""
        if sim_func is None:
            sim_func = self.cosine_similarity
        if user not in self.user_ratings:
            return []

        # 1. 计算与其他用户的相似度
        target_vec = self.user_ratings[user]
        sims = []
        for other, other_vec in self.user_ratings.items():
            if other == user:
                continue
            s = sim_func(target_vec, other_vec)
            if s > 0:
                sims.append((other, s))
        sims.sort(key=lambda x: -x[1])
        sims = sims[:k_neighbors]

        # 2. 加权预测评分
        seen = set(target_vec)
        scores = defaultdict(float)
        weight_sum = defaultdict(float)
        for other, s in sims:
            for item, rating in self.user_ratings[other].items():
                if item in seen:
                    continue
                scores[item] += s * rating
                weight_sum[item] += s

        result = []
        for item, score in scores.items():
            if weight_sum[item] > 0:
                result.append((item, score / weight_sum[item]))
        result.sort(key=lambda x: -x[1])
        return result[:top_n]

    # ---------- 基于物品的 CF ----------
    def item_based_recommend(self, user, top_n=5, k_neighbors=10, sim_func=None):
        """为指定用户推荐 top_n 个物品（基于物品相似度）"""
        if sim_func is None:
            sim_func = self.cosine_similarity
        if user not in self.user_ratings:
            return []

        seen = self.user_ratings[user]
        scores = defaultdict(float)
        weight_sum = defaultdict(float)

        # 对用户已评分的每个物品，找最相似的物品
        for item, rating in seen.items():
            sims = []
            for other_item, other_vec in self.item_ratings.items():
                if other_item == item or other_item in seen:
                    continue
                s = sim_func(self.item_ratings[item], other_vec)
                if s > 0:
                    sims.append((other_item, s))
            sims.sort(key=lambda x: -x[1])
            for other_item, s in sims[:k_neighbors]:
                scores[other_item] += s * rating
                weight_sum[other_item] += s

        result = []
        for item, score in scores.items():
            if weight_sum[item] > 0:
                result.append((item, score / weight_sum[item]))
        result.sort(key=lambda x: -x[1])
        return result[:top_n]


def demo():
    # 用户对电影的评分（1-5）
    data = [
        ("Alice",   "星际穿越",  5),
        ("Alice",   "盗梦空间",  4),
        ("Alice",   "泰坦尼克",  3),
        ("Bob",     "星际穿越",  4),
        ("Bob",     "盗梦空间",  5),
        ("Bob",     "黑客帝国",  5),
        ("Carol",   "泰坦尼克",  5),
        ("Carol",   "罗马假日",  4),
        ("Carol",   "盗梦空间",  3),
        ("Dave",    "星际穿越",  4),
        ("Dave",    "黑客帝国",  4),
        ("Dave",    "罗马假日",  2),
        ("Eve",     "盗梦空间",  4),
        ("Eve",     "黑客帝国",  5),
        ("Eve",     "泰坦尼克",  2),
    ]

    cf = CollaborativeFiltering()
    cf.load_data(data)

    print("=" * 50)
    print("基于用户的协同过滤 - 为 Alice 推荐:")
    for item, score in cf.user_based_recommend("Alice", top_n=3):
        print(f"  {item}: 预测评分 {score:.3f}")

    print("\n基于物品的协同过滤 - 为 Alice 推荐:")
    for item, score in cf.item_based_recommend("Alice", top_n=3):
        print(f"  {item}: 预测评分 {score:.3f}")

    print("\n基于用户(皮尔逊) - 为 Bob 推荐:")
    for item, score in cf.user_based_recommend(
        "Bob", top_n=3, sim_func=cf.pearson_similarity
    ):
        print(f"  {item}: 预测评分 {score:.3f}")
    print("=" * 50)


if __name__ == "__main__":
    demo()
