"""
简单聊天机器人（规则型）
功能：基于模式匹配（正则）的规则型聊天机器人，支持上下文记忆、
      关键词触发、变量替换、随机回复、情绪识别、闲聊扩展、
      多轮对话状态等
"""

import re
import random
import time
from datetime import datetime


class ChatBot:
    """规则型聊天机器人"""

    def __init__(self, name: str = "小智"):
        self.name = name
        # 用户信息记忆（如姓名）
        self.memory = {}
        # 对话历史
        self.history = []
        # 上下文状态：用于多轮对话（如询问名字时设置 awaiting_name）
        self.context = None
        # 启动时间
        self.start_time = datetime.now()

        # 规则列表：(模式列表, 回复列表 或 回调函数, 优先级)
        self.rules = []
        self._init_default_rules()

    # ==================== 规则注册 ====================

    def add_rule(self, patterns, responses, priority: int = 0):
        """添加规则
        patterns: 正则模式字符串或列表
        responses: 回复字符串列表，或回调函数 fn(match, bot) -> str
        priority: 优先级，数值越大越优先
        """
        if isinstance(patterns, str):
            patterns = [patterns]
        compiled = [re.compile(p, re.IGNORECASE) for p in patterns]
        self.rules.append((compiled, responses, priority))
        # 按优先级降序
        self.rules.sort(key=lambda r: -r[2])

    def _init_default_rules(self):
        """初始化默认规则"""

        # 问候
        self.add_rule(
            [r"\b(hi|hello|hey)\b", r"你好|您好|嗨|哈喽"],
            [
                "你好！我是{bot_name}，很高兴见到你。",
                "嗨！今天过得怎么样？",
                "您好，有什么我可以帮您的吗？",
            ],
            priority=10,
        )

        # 询问名字
        self.add_rule(
            [r"你叫什么", r"你是谁", r"你的名字", r"what.*your name"],
            [
                "我是 {bot_name}，一个简单的规则型聊天机器人～",
                "我叫 {bot_name}，请多指教。",
            ],
            priority=10,
        )

        # 用户告诉名字 - 使用回调
        self.add_rule(
            [r"我叫(.+)", r"我的名字是(.+)", r"my name is (.+)"],
            self._handle_user_name,
            priority=20,
        )

        # 询问用户名字
        self.add_rule(
            [r"我是谁", r"还记得我吗", r"你知道我.*名字"],
            self._handle_recall_name,
            priority=15,
        )

        # 时间日期
        self.add_rule(
            [r"现在.*几点|时间", r"what time"],
            self._handle_time,
            priority=10,
        )
        self.add_rule(
            [r"今天.*几号|日期|今天.*星期"],
            self._handle_date,
            priority=10,
        )

        # 数学
        self.add_rule(
            [r"(\d+(?:\.\d+)?)\s*([+\-*/])\s*(\d+(?:\.\d+)?)"],
            self._handle_math,
            priority=15,
        )

        # 情绪
        self.add_rule(
            [r"难过|伤心|不开心|郁闷|sad|unhappy"],
            [
                "抱抱～发生什么事了？说出来或许会好一点。",
                "听到你这样我也有点心疼，要不要聊聊？",
                "心情不好的时候，做点喜欢的事情试试看吧。",
            ],
            priority=8,
        )

        self.add_rule(
            [r"开心|高兴|快乐|哈哈|happy|great"],
            [
                "看到你开心我也很开心！",
                "哈哈，分享一下让你开心的事情吧～",
                "保持好心情，每天都美美的！",
            ],
            priority=8,
        )

        self.add_rule(
            [r"生气|愤怒|烦|讨厌|angry|annoyed"],
            [
                "深呼吸，慢慢来，别让坏情绪占据你。",
                "发生什么了？跟我说说看吧。",
            ],
            priority=8,
        )

        # 感谢
        self.add_rule(
            [r"谢谢|多谢|thank|thanks"],
            ["不客气！", "举手之劳，应该的。", "能帮到你就好～"],
            priority=10,
        )

        # 道歉
        self.add_rule(
            [r"对不起|抱歉|不好意思|sorry"],
            ["没关系，没事的～", "别在意啦。"],
            priority=10,
        )

        # 再见
        self.add_rule(
            [r"再见|拜拜|bye|goodbye|88"],
            ["再见！期待下次再聊～", "拜拜，记得照顾好自己。", "Bye~ 祝你今天愉快！"],
            priority=10,
        )

        # 帮助
        self.add_rule(
            [r"^帮助$|^help$|你能.*什么|功能"],
            self._handle_help,
            priority=10,
        )

        # 天气（无真实数据）
        self.add_rule(
            [r"天气|下雨|温度"],
            [
                "我没有联网功能，没法查实时天气，建议看看天气预报哦~",
                "今天的天气...你看窗外就知道啦！",
            ],
            priority=5,
        )

        # 笑话
        self.add_rule(
            [r"讲.*笑话|说.*段子|笑话"],
            [
                "为什么程序员喜欢黑色？因为他们不喜欢 light 模式。",
                "0 对 8 说：胖就胖嘛，干嘛系腰带。",
                "我有一个 Java 笑话，但是 GC 了。",
            ],
            priority=10,
        )

        # 编程问题
        self.add_rule(
            [r"python|编程|代码|程序"],
            [
                "Python 是一门简洁优雅的语言，多写多练！",
                "编程嘛，关键是理解问题然后拆解它。",
                "遇到 bug 不要慌，先打个断点再说。",
            ],
            priority=5,
        )

        # 关于自己
        self.add_rule(
            [r"你.*多大|你年龄"],
            self._handle_age,
            priority=8,
        )

        # 重复 / 模仿（echo）
        self.add_rule(
            [r"^重复\s*(.+)", r"^repeat\s+(.+)"],
            lambda m, bot: f"{m.group(1)}",
            priority=15,
        )

        # 默认兜底回复
        self.add_rule(
            [r".*"],
            [
                "嗯嗯，我在听～",
                "这个话题我不太懂，可以换个聊聊吗？",
                "有意思，能详细说说吗？",
                "我是规则型机器人，理解能力有限，请多包涵～",
                "({bot_name} 歪头思考中...)",
            ],
            priority=-100,
        )

    # ==================== 内置回调 ====================

    def _handle_user_name(self, match, bot):
        name = match.group(1).strip().rstrip("。.,!?！？")
        # 清理多余尾部
        name = re.split(r"[，,。.！!？?\s]", name)[0]
        if name:
            self.memory["user_name"] = name
            return random.choice([
                f"你好，{name}！很高兴认识你。",
                f"{name}，名字真好听～",
                f"记住啦，你叫 {name}。",
            ])
        return "你叫什么名字呢？"

    def _handle_recall_name(self, match, bot):
        name = self.memory.get("user_name")
        if name:
            return f"当然记得，你是 {name} 呀！"
        return "嗯…我们好像还没正式介绍呢，你叫什么名字？"

    def _handle_time(self, match, bot):
        return f"现在是 {datetime.now().strftime('%H:%M:%S')}。"

    def _handle_date(self, match, bot):
        now = datetime.now()
        weekdays = ["一", "二", "三", "四", "五", "六", "日"]
        return (f"今天是 {now.strftime('%Y年%m月%d日')}，"
                f"星期{weekdays[now.weekday()]}。")

    def _handle_math(self, match, bot):
        a = float(match.group(1))
        op = match.group(2)
        b = float(match.group(3))
        try:
            if op == "+":
                r = a + b
            elif op == "-":
                r = a - b
            elif op == "*":
                r = a * b
            elif op == "/":
                if b == 0:
                    return "除数不能为零哦～"
                r = a / b
            else:
                return "我不会这种运算诶。"
            # 整数显示为整数
            if r == int(r):
                r = int(r)
            return f"{a:g} {op} {b:g} = {r}"
        except Exception:
            return "算的时候出错了，再试一次？"

    def _handle_help(self, match, bot):
        return (
            f"我是 {self.name}，可以聊聊：\n"
            "  - 问候、自我介绍\n"
            "  - 当前时间和日期\n"
            "  - 简单四则运算（如 12 + 34）\n"
            "  - 讲笑话、聊心情\n"
            "  - 记住你的名字\n"
            "  - 输入“重复 xxx”让我复读\n"
            "  - 输入 quit/exit 退出"
        )

    def _handle_age(self, match, bot):
        delta = datetime.now() - self.start_time
        secs = int(delta.total_seconds())
        return f"我刚出生 {secs} 秒，是个新生小机器人～"

    # ==================== 回复 ====================

    def respond(self, text: str) -> str:
        """对单条消息生成回复"""
        text = text.strip()
        if not text:
            return "嗯？你想说什么呢？"

        for patterns, responses, _priority in self.rules:
            for pat in patterns:
                m = pat.search(text)
                if m:
                    if callable(responses):
                        reply = responses(m, self)
                    else:
                        reply = random.choice(responses)
                    reply = self._render(reply)
                    self.history.append({"user": text, "bot": reply,
                                         "time": datetime.now().isoformat()})
                    return reply

        # 理论上兜底规则会匹配，所以走不到这里
        return "..."

    def _render(self, template: str) -> str:
        """变量替换"""
        return template.format(
            bot_name=self.name,
            user_name=self.memory.get("user_name", "朋友"),
        )

    # ==================== 会话管理 ====================

    def chat(self):
        """启动交互式聊天"""
        print(f"=== {self.name} 已上线，输入 quit/exit 退出 ===")
        print(f"{self.name}: 你好呀！想聊什么？")
        while True:
            try:
                user_input = input("你: ").strip()
            except (EOFError, KeyboardInterrupt):
                print(f"\n{self.name}: 拜拜～")
                break
            if user_input.lower() in ("quit", "exit", "退出"):
                print(f"{self.name}: 期待下次再聊～")
                break
            if not user_input:
                continue
            reply = self.respond(user_input)
            print(f"{self.name}: {reply}")

    def stats(self) -> dict:
        """对话统计"""
        return {
            "name": self.name,
            "rules": len(self.rules),
            "messages": len(self.history),
            "memory": dict(self.memory),
            "uptime_seconds": int((datetime.now() - self.start_time).total_seconds()),
        }


# ==================== 演示 ====================

def run_scripted_demo(bot: ChatBot, scripts: list):
    """以脚本方式模拟用户对话"""
    for utterance in scripts:
        print(f"  你: {utterance}")
        reply = bot.respond(utterance)
        print(f"  {bot.name}: {reply}")
        time.sleep(0.05)


if __name__ == "__main__":
    print("=" * 60)
    print("  简单聊天机器人（规则型）Demo")
    print("=" * 60)

    random.seed(42)  # 让回复可重现
    bot = ChatBot(name="小智")

    # 1. 问候
    print("\n--- 1. 问候和自我介绍 ---")
    run_scripted_demo(bot, [
        "你好",
        "你叫什么名字？",
        "我叫张三",
        "我是谁？",
    ])

    # 2. 时间和日期
    print("\n--- 2. 时间和日期 ---")
    run_scripted_demo(bot, [
        "现在几点？",
        "今天几号？",
    ])

    # 3. 数学计算
    print("\n--- 3. 简单计算 ---")
    run_scripted_demo(bot, [
        "12 + 34",
        "100 - 7",
        "6 * 7",
        "10 / 3",
        "5 / 0",
    ])

    # 4. 情绪识别
    print("\n--- 4. 情绪识别 ---")
    run_scripted_demo(bot, [
        "今天有点难过",
        "刚才中了彩票，超开心",
        "气死我了！",
    ])

    # 5. 笑话和帮助
    print("\n--- 5. 闲聊功能 ---")
    run_scripted_demo(bot, [
        "讲个笑话",
        "你能做什么？",
        "重复 我爱学习",
        "你多大了？",
    ])

    # 6. 兜底回复
    print("\n--- 6. 兜底（未识别）回复 ---")
    run_scripted_demo(bot, [
        "asdfgh",
        "量子纠缠是什么原理？",
    ])

    # 7. 道别
    print("\n--- 7. 道别 ---")
    run_scripted_demo(bot, [
        "谢谢你",
        "再见",
    ])

    # 8. 自定义新规则
    print("\n--- 8. 用户自定义规则 ---")
    bot.add_rule(
        [r"喜欢.*猫|cat"],
        ["喵～我也是猫派！", "猫猫最可爱了！"],
        priority=20,
    )
    run_scripted_demo(bot, [
        "我超喜欢猫",
    ])

    # 9. 状态统计
    print("\n--- 9. 机器人状态 ---")
    for k, v in bot.stats().items():
        print(f"  {k}: {v}")

    print("\n" + "=" * 60)
    print("  Demo 运行完毕！")
    print("=" * 60)
    print("\n要进入交互模式，运行：")
    print("  bot = ChatBot('小智'); bot.chat()")
