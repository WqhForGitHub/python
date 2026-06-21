"""
聊天机器人（NLP）- 纯 Python 实现
=====================================
基于 TF-IDF + 余弦相似度的检索式聊天机器人。
支持：
- 意图匹配（FAQ 知识库检索）
- 模糊匹配（找最相似的问题）
- 简单对话状态（上下文记忆）
- 基础规则模板（问候、时间、计算）
"""

import math
import re
import datetime
from collections import Counter, defaultdict


def tokenize(text):
    """简单中英文混合分词：英文按空格，中文按字"""
    text = text.lower()
    return re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]", text)


# ---------- TF-IDF 引擎 ----------
class TfidfEngine:
    def __init__(self):
        self.docs = []          # 原始问题列表
        self.answers = []       # 对应答案
        self.doc_tokens = []    # 分词结果
        self.df = Counter()     # 文档频率
        self.idf = {}
        self.tfidf_vecs = []

    def add_qa(self, question, answer):
        self.docs.append(question)
        self.answers.append(answer)

    def build(self):
        self.doc_tokens = [tokenize(d) for d in self.docs]
        self.df.clear()
        for toks in self.doc_tokens:
            for w in set(toks):
                self.df[w] += 1
        n = len(self.docs)
        self.idf = {w: math.log((n + 1) / (df + 1)) + 1 for w, df in self.df.items()}
        self.tfidf_vecs = [self._tfidf(toks) for toks in self.doc_tokens]

    def _tfidf(self, tokens):
        tf = Counter(tokens)
        total = sum(tf.values()) or 1
        return {w: (c / total) * self.idf.get(w, 0) for w, c in tf.items()}

    @staticmethod
    def cosine(v1, v2):
        common = set(v1) & set(v2)
        if not common:
            return 0.0
        dot = sum(v1[w] * v2[w] for w in common)
        n1 = math.sqrt(sum(v * v for v in v1.values()))
        n2 = math.sqrt(sum(v * v for v in v2.values()))
        if n1 == 0 or n2 == 0:
            return 0.0
        return dot / (n1 * n2)

    def search(self, query, top_k=1):
        q_vec = self._tfidf(tokenize(query))
        scores = [(i, self.cosine(q_vec, v)) for i, v in enumerate(self.tfidf_vecs)]
        scores.sort(key=lambda x: -x[1])
        return scores[:top_k]


# ---------- 聊天机器人 ----------
class ChatBot:
    def __init__(self, name="小智"):
        self.name = name
        self.engine = TfidfEngine()
        self.context = {"last_topic": None}
        self.rules = []  # [(pattern, handler)]
        self._init_rules()
        self._init_kb()
        self.engine.build()

    def _init_rules(self):
        self.rules.append((r"(你好|hi|hello|嗨)", self._greet))
        self.rules.append((r"(再见|拜拜|bye)", self._bye))
        self.rules.append((r"(几点|时间|now|time)", self._time))
        self.rules.append((r"(日期|今天|date|today)", self._date))
        self.rules.append((r"^计算\s*(.+)$", self._calc))
        self.rules.append((r"你叫什么|你是谁|你的名字", self._self_intro))

    def _init_kb(self):
        kb = [
            ("Python 是什么", "Python 是一门简洁、高效的解释型编程语言，常用于数据分析、Web 开发、AI 等领域。"),
            ("怎么学 Python", "建议先掌握基础语法，再做小项目练手，多读优秀源码，坚持每天写代码。"),
            ("什么是机器学习", "机器学习是通过数据训练模型，让计算机自动学习规律并做出预测的方法。"),
            ("什么是深度学习", "深度学习是机器学习的一个分支，使用多层神经网络从大量数据中学习复杂模式。"),
            ("什么是协同过滤", "协同过滤是推荐系统的常用算法，通过用户/物品相似度来预测用户可能喜欢的物品。"),
            ("如何提高编程能力", "多写代码、多读源码、多思考、多重构。理论与实践结合，遇到问题积极调试。"),
            ("天气怎么样", "我无法连接互联网查询实时天气，建议你查看天气 App。"),
            ("吃什么好", "可以吃点清淡的，蔬菜水果均衡搭配，记得多喝水。"),
        ]
        for q, a in kb:
            self.engine.add_qa(q, a)

    # ---- 规则处理器 ----
    def _greet(self, m):
        return f"你好！我是 {self.name}，有什么可以帮你的？"

    def _bye(self, m):
        return "再见！期待下次和你聊天～"

    def _time(self, m):
        return f"现在时间是 {datetime.datetime.now().strftime('%H:%M:%S')}"

    def _date(self, m):
        return f"今天是 {datetime.date.today().strftime('%Y-%m-%d')}"

    def _calc(self, m):
        expr = m.group(1).strip()
        if not re.match(r"^[\d\s\+\-\*/\.\(\)]+$", expr):
            return "我只能计算数字与 + - * / 的组合哦"
        try:
            return f"结果是 {eval(expr)}"
        except Exception:
            return "计算出错了，请检查表达式。"

    def _self_intro(self, m):
        return f"我是 {self.name}，一个用纯 Python 实现的聊天机器人。"

    # ---- 主逻辑 ----
    def reply(self, text):
        text = text.strip()
        if not text:
            return "你想问什么呢？"

        # 1) 规则匹配
        for pat, handler in self.rules:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return handler(m)

        # 2) 知识库检索
        results = self.engine.search(text, top_k=1)
        if results and results[0][1] > 0.15:
            idx = results[0][0]
            self.context["last_topic"] = self.engine.docs[idx]
            return self.engine.answers[idx]

        # 3) 兜底
        return "这个问题我还不太懂呢，你可以换个说法试试～"


def demo():
    bot = ChatBot()
    print("=" * 50)
    print(f"{bot.name}：你好！我是聊天机器人，输入 '退出' 结束。")
    print("=" * 50)

    test_inputs = [
        "你好！",
        "你叫什么名字",
        "Python 好学吗",
        "什么是机器学习",
        "现在几点了",
        "计算 (3+5)*2",
        "天气怎么样",
        "再见",
    ]
    for q in test_inputs:
        print(f"我：{q}")
        print(f"{bot.name}：{bot.reply(q)}\n")

    # 交互模式（按需取消注释）
    # while True:
    #     try:
    #         q = input("我：")
    #     except EOFError:
    #         break
    #     if q.strip() in {"退出", "exit", "quit"}:
    #         print(f"{bot.name}：再见！")
    #         break
    #     print(f"{bot.name}：{bot.reply(q)}")


if __name__ == "__main__":
    demo()
