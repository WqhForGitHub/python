"""
情感分析工具（NLP）- 纯 Python 实现
=====================================
基于情感词典 + 朴素贝叶斯分类器的混合方案。

特点：
- 中英文均可（这里以中文短语为示例，可换词典扩展）
- 支持否定词、程度副词
- 提供 Naive Bayes 训练接口
"""

import math
import re
from collections import defaultdict, Counter


# ---------- 情感词典法 ----------
class LexiconSentiment:
    """基于词典的情感打分器"""

    DEFAULT_POS = {
        "好": 1, "棒": 2, "喜欢": 2, "优秀": 2, "推荐": 1,
        "完美": 3, "满意": 2, "开心": 2, "爱": 2, "高兴": 2,
        "good": 1, "great": 2, "excellent": 3, "love": 2, "happy": 2,
    }
    DEFAULT_NEG = {
        "差": -2, "糟糕": -2, "讨厌": -2, "失望": -2, "烂": -3,
        "难看": -2, "差劲": -3, "气愤": -2, "生气": -2, "无聊": -1,
        "bad": -1, "terrible": -3, "hate": -2, "awful": -3, "boring": -1,
    }
    NEGATIONS = {"不", "没", "无", "非", "莫", "勿", "not", "no", "never"}
    DEGREE = {
        "非常": 1.5, "很": 1.3, "极其": 2.0, "特别": 1.5, "稍微": 0.7,
        "有点": 0.7, "一点": 0.7,
        "very": 1.3, "extremely": 2.0, "slightly": 0.7,
    }

    def __init__(self, pos=None, neg=None):
        self.pos = pos or dict(self.DEFAULT_POS)
        self.neg = neg or dict(self.DEFAULT_NEG)

    def tokenize(self, text):
        """简单分词：中文按字 + 词典里多字词；英文按空格"""
        tokens = []
        i = 0
        text = text.lower()
        while i < len(text):
            ch = text[i]
            if re.match(r"[a-zA-Z]", ch):
                m = re.match(r"[a-zA-Z]+", text[i:])
                tokens.append(m.group())
                i += len(m.group())
            elif re.match(r"\s", ch) or re.match(r"[，。！？,.!?]", ch):
                i += 1
            else:
                # 中文：尝试匹配词典中最长的词
                matched = None
                for length in range(4, 0, -1):
                    word = text[i:i + length]
                    if (word in self.pos or word in self.neg
                            or word in self.NEGATIONS or word in self.DEGREE):
                        matched = word
                        break
                if matched:
                    tokens.append(matched)
                    i += len(matched)
                else:
                    tokens.append(ch)
                    i += 1
        return tokens

    def score(self, text):
        """返回情感分值；>0 偏正，<0 偏负"""
        tokens = self.tokenize(text)
        total = 0.0
        i = 0
        while i < len(tokens):
            tok = tokens[i]
            base = self.pos.get(tok, 0) + self.neg.get(tok, 0)
            if base != 0:
                weight = 1.0
                negate = False
                # 向前看 2 个 token，找否定词和程度副词
                for j in range(max(0, i - 2), i):
                    t = tokens[j]
                    if t in self.NEGATIONS:
                        negate = not negate
                    if t in self.DEGREE:
                        weight *= self.DEGREE[t]
                if negate:
                    base = -base
                total += base * weight
            i += 1
        return total

    def classify(self, text):
        s = self.score(text)
        if s > 0.5:
            return "正面", s
        elif s < -0.5:
            return "负面", s
        return "中性", s


# ---------- 朴素贝叶斯分类器 ----------
class NaiveBayesSentiment:
    def __init__(self):
        self.class_counts = Counter()
        self.word_counts = defaultdict(Counter)  # cls -> word -> count
        self.vocab = set()

    @staticmethod
    def tokenize(text):
        text = text.lower()
        return re.findall(r"[a-z]+|[\u4e00-\u9fff]", text)

    def train(self, samples):
        """samples: [(text, label), ...]"""
        for text, label in samples:
            self.class_counts[label] += 1
            for w in self.tokenize(text):
                self.word_counts[label][w] += 1
                self.vocab.add(w)

    def predict(self, text):
        """带拉普拉斯平滑的对数概率"""
        words = self.tokenize(text)
        total_docs = sum(self.class_counts.values())
        best, best_lp = None, -float("inf")
        v = len(self.vocab)
        for cls, n_cls in self.class_counts.items():
            log_p = math.log(n_cls / total_docs)
            total_words = sum(self.word_counts[cls].values())
            for w in words:
                c = self.word_counts[cls].get(w, 0)
                log_p += math.log((c + 1) / (total_words + v))
            if log_p > best_lp:
                best_lp = log_p
                best = cls
        return best, best_lp


def demo():
    print("=" * 50)
    print("【词典法】情感分析示例")
    lex = LexiconSentiment()
    samples = [
        "这部电影非常好看，我很喜欢！",
        "服务太差劲了，特别失望。",
        "还可以吧，没什么特别的。",
        "I love this product, it is excellent!",
        "This is a terrible experience, I hate it.",
        "不好看，很无聊",
    ]
    for s in samples:
        label, score = lex.classify(s)
        print(f"  [{label:>2s}] ({score:+.2f})  {s}")

    print("\n【朴素贝叶斯】训练 + 分类示例")
    train_data = [
        ("这部电影真好看 我很喜欢", "pos"),
        ("演员演技棒 推荐大家去看", "pos"),
        ("剧情非常精彩 完美", "pos"),
        ("这是一部烂片 太失望了", "neg"),
        ("剧情无聊 浪费时间", "neg"),
        ("演技差劲 不推荐", "neg"),
    ]
    nb = NaiveBayesSentiment()
    nb.train(train_data)
    tests = ["剧情精彩 演技好", "无聊 烂片 失望", "完美 喜欢 推荐"]
    for t in tests:
        label, lp = nb.predict(t)
        print(f"  [{label}] (logP={lp:.2f})  {t}")
    print("=" * 50)


if __name__ == "__main__":
    demo()
