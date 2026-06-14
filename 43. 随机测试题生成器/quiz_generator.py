"""
随机测试题生成器
功能：
    - 自动生成数学题（加减乘除、混合）
    - 单选题（基于题库随机抽题、选项随机打乱）
    - 填空题
    - 支持难度等级（数字范围、运算符种类）
    - 自动评分、显示错题
    - 可导出试卷文本
"""

import os
import random
import string


# ============= 数学题生成 =============

class MathQuestion:
    """数学题"""

    OPS = {
        "+": lambda a, b: a + b,
        "-": lambda a, b: a - b,
        "*": lambda a, b: a * b,
        "/": lambda a, b: a // b,
    }

    def __init__(self, difficulty: str = "easy"):
        self.difficulty = difficulty
        self.expr, self.answer = self._gen()

    def _gen(self):
        if self.difficulty == "easy":
            ops = ["+", "-"]
            lo, hi = 1, 20
        elif self.difficulty == "medium":
            ops = ["+", "-", "*"]
            lo, hi = 1, 50
        else:
            ops = ["+", "-", "*", "/"]
            lo, hi = 2, 100

        op = random.choice(ops)
        if op == "/":
            # 保证整除
            b = random.randint(lo, hi // 2)
            ans = random.randint(lo, hi // 2)
            a = b * ans
            return f"{a} ÷ {b}", ans
        a = random.randint(lo, hi)
        b = random.randint(lo, hi)
        if op == "-" and b > a:
            a, b = b, a
        ans = self.OPS[op](a, b)
        sign = {"*": "×", "+": "+", "-": "-"}.get(op, op)
        return f"{a} {sign} {b}", ans

    def check(self, user_answer) -> bool:
        try:
            return int(user_answer) == self.answer
        except (ValueError, TypeError):
            return False

    def __str__(self):
        return f"{self.expr} = ?"


# ============= 单选题题库 =============

CHOICE_BANK = [
    {
        "q": "Python 中用于定义函数的关键字是？",
        "options": ["def", "func", "function", "lambda"],
        "answer": 0,
    },
    {
        "q": "下面哪个是 Python 不可变类型？",
        "options": ["list", "dict", "set", "tuple"],
        "answer": 3,
    },
    {
        "q": "下列哪个是合法的 Python 标识符？",
        "options": ["2name", "my-var", "_value", "class"],
        "answer": 2,
    },
    {
        "q": "len('hello') 的结果是？",
        "options": ["4", "5", "6", "报错"],
        "answer": 1,
    },
    {
        "q": "执行 print(2 ** 3) 输出？",
        "options": ["6", "8", "9", "23"],
        "answer": 1,
    },
    {
        "q": "下列哪个不是循环语句？",
        "options": ["for", "while", "do-while", "以上都是"],
        "answer": 2,
    },
    {
        "q": "字典的方法 .keys() 返回？",
        "options": ["列表", "元组", "视图对象", "字符串"],
        "answer": 2,
    },
    {
        "q": "Python 中读取文件的内置函数是？",
        "options": ["open", "read", "load", "fopen"],
        "answer": 0,
    },
]


class ChoiceQuestion:
    def __init__(self, item: dict):
        self.q = item["q"]
        # 打乱选项，记录新的正确索引
        opts = list(enumerate(item["options"]))
        random.shuffle(opts)
        self.options = [o[1] for o in opts]
        self.answer = next(i for i, o in enumerate(opts) if o[0] == item["answer"])

    def check(self, user) -> bool:
        try:
            if isinstance(user, str) and user.upper() in "ABCDEFGH":
                return ord(user.upper()) - ord("A") == self.answer
            return int(user) == self.answer
        except (ValueError, TypeError):
            return False

    def __str__(self):
        s = [self.q]
        for i, opt in enumerate(self.options):
            s.append(f"  {chr(ord('A') + i)}. {opt}")
        return "\n".join(s)


# ============= 填空题 =============

FILL_BANK = [
    ("Python 中表示空值的关键字是 ___ 。", "None"),
    ("将字符串转为整数的内置函数是 ___ 。", "int"),
    ("用于异常捕获的关键字是 try / ___ 。", "except"),
    ("列表推导式 [x*2 for x in range(3)] 结果是 ___ 。", "[0, 2, 4]"),
    ("布尔类型只有两个值: True 和 ___ 。", "False"),
]


class FillQuestion:
    def __init__(self, item):
        self.q, self.answer = item

    def check(self, user) -> bool:
        return str(user).strip().lower() == self.answer.lower()

    def __str__(self):
        return self.q


# ============= 试卷 =============

class QuizPaper:
    def __init__(self, difficulty: str = "easy"):
        self.questions = []
        self.user_answers = []
        self.difficulty = difficulty

    def generate(self, n_math=5, n_choice=3, n_fill=2):
        for _ in range(n_math):
            self.questions.append(MathQuestion(self.difficulty))
        for item in random.sample(CHOICE_BANK, k=min(n_choice, len(CHOICE_BANK))):
            self.questions.append(ChoiceQuestion(item))
        for item in random.sample(FILL_BANK, k=min(n_fill, len(FILL_BANK))):
            self.questions.append(FillQuestion(item))
        random.shuffle(self.questions)

    def submit(self, answers: list) -> dict:
        """传入答案列表，返回评分结果"""
        self.user_answers = answers
        correct = 0
        wrongs = []
        for i, (q, a) in enumerate(zip(self.questions, answers), 1):
            if q.check(a):
                correct += 1
            else:
                wrongs.append((i, q, a))
        total = len(self.questions)
        return {
            "total": total,
            "correct": correct,
            "score": round(correct / total * 100, 1) if total else 0,
            "wrongs": wrongs,
        }

    def render(self) -> str:
        out = [f"=== 测验试卷（难度: {self.difficulty}） ==="]
        for i, q in enumerate(self.questions, 1):
            out.append(f"\n第 {i} 题:")
            out.append(str(q))
            out.append("答案: ____")
        return "\n".join(out)


# ==================== Demo ====================

def auto_solve(q):
    """模拟一个有 70% 正确率的考生"""
    if random.random() < 0.7:
        if isinstance(q, MathQuestion):
            return q.answer
        if isinstance(q, ChoiceQuestion):
            return q.answer
        if isinstance(q, FillQuestion):
            return q.answer
    # 给个错误答案
    if isinstance(q, MathQuestion):
        return q.answer + random.choice([-1, 1, 2])
    if isinstance(q, ChoiceQuestion):
        return (q.answer + 1) % len(q.options)
    return "wrong"


if __name__ == "__main__":
    print("=" * 60)
    print("  随机测试题生成器 Demo")
    print("=" * 60)

    random.seed(42)

    # 1. 生成试卷
    print("\n--- 1. 生成试卷（中等难度，5+3+2 = 10 题） ---")
    paper = QuizPaper(difficulty="medium")
    paper.generate(n_math=5, n_choice=3, n_fill=2)
    print(paper.render())

    # 2. 模拟答题
    print("\n--- 2. 模拟考生作答 ---")
    answers = [auto_solve(q) for q in paper.questions]
    for i, a in enumerate(answers, 1):
        print(f"  第{i}题答: {a}")

    # 3. 评分
    print("\n--- 3. 评分 ---")
    res = paper.submit(answers)
    print(f"  总题数: {res['total']}")
    print(f"  正确数: {res['correct']}")
    print(f"  得分:   {res['score']}/100")
    if res["wrongs"]:
        print("\n  错题：")
        for idx, q, a in res["wrongs"]:
            corr = q.answer if not isinstance(q, ChoiceQuestion) else \
                   chr(ord('A') + q.answer)
            print(f"    第{idx}题  你的答: {a}   正确答: {corr}")

    # 4. 不同难度数学题示例
    print("\n--- 4. 不同难度数学题示例 ---")
    for diff in ("easy", "medium", "hard"):
        q = MathQuestion(diff)
        print(f"  [{diff:<6}] {q}  =>  {q.answer}")

    # 5. 导出试卷文本
    print("\n--- 5. 导出试卷 ---")
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "quiz_export.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write(paper.render())
    print(f"  已导出: {out}  ({os.path.getsize(out)} bytes)")
    os.remove(out)

    print("\n" + "=" * 60)
    print("  Demo 运行完毕！")
    print("=" * 60)
