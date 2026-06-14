"""
简单聊天机器人（规则型）
功能：
    - 基于关键词与正则规则匹配
    - 支持模糊匹配（同义词替换、忽略大小写、去标点）
    - 支持上下文（记住上一个话题）
    - 支持变量提取，如 "我叫张三" -> 记住名字
    - 内置常见对话场景：问候、天气、时间、心情、闲聊、再见
    - 不命中规则时回退到默认应答
"""

import re
import random
import string
from datetime import datetime


# 同义词归一化表
SYNONYMS = {
    "您": "你",
    "咋": "怎么",
    "啥": "什么",
    "嘛": "什么",
    "么": "吗",
    "拜拜": "再见",
    "byebye": "再见",
    "bye": "再见",
    "hi": "你好",
    "hello": "你好",
    "hey": "你好",
}


# 规则: (正则模式, 回复列表) - 顺序敏感
RULES = [
    (r"(你好|您好|嗨|早上好|晚上好|下午好)",
     ["你好呀！", "嗨，很高兴见到你！", "你好，今天过得怎么样？"]),
    (r"(再见|拜拜|goodbye|88)",
     ["再见，有空再聊~", "拜拜，祝你今天愉快！", "下次见！"]),
    (r"我叫(.+)|我的名字(?:是|叫)(.+)",
     ["{name}，这名字真好听！", "认识你，{name}！", "你好，{name}~"]),
    (r"你(叫什么|是谁)",
     ["我是 PyBot，一个简单的规则型聊天机器人。",
      "你可以叫我 PyBot~"]),
    (r"(几点|现在时间|时间)",
     ["现在是 {time}", "时间显示：{time}"]),
    (r"(今天|现在).*(日期|几号|星期)",
     ["今天是 {date}", "日期：{date}"]),
    (r"(天气|下雨|温度)",
     ["我没法联网查天气，但希望你那边阳光明媚！",
      "天气这事儿，问问窗外吧~"]),
    (r"(讲个笑话|说个笑话|笑话)",
     ["程序员最爱的咖啡是？——Java！",
      "我有一个关于 UDP 的笑话，但你不一定能收到。",
      "为什么程序员分不清万圣节和圣诞节？因为 Oct 31 == Dec 25。"]),
    (r"(我|心情).*(开心|高兴|快乐|爽)",
     ["真为你高兴！继续保持~", "听起来不错呀！"]),
    (r"(我|心情).*(难过|伤心|沮丧|累|不开心)",
     ["抱抱，会好起来的。", "深呼吸一下，事情没那么糟。",
      "需要的话可以和我聊聊~"]),
    (r"(谢谢|感谢|thanks|thx)",
     ["不客气~", "举手之劳！", "随时为你服务！"]),
    (r"(你会(什么|啥)|帮助|help)",
     ["我能闲聊、报时、讲笑话，还能记住你的名字。试试看吧！"]),
    (r"\d+\s*[\+\-\*/]\s*\d+",
     ["看起来像道算术题，要不你按计算器吧？"]),
]


DEFAULT_REPLIES = [
    "嗯嗯，我在听。",
    "可以详细说说吗？",
    "有意思，再讲讲？",
    "我没太明白，能换种说法吗？",
    "（思考中…）",
]


class ChatBot:
    def __init__(self, name: str = "PyBot"):
        self.name = name
        self.context = {}      # 用户变量: name, last_topic ...
        self.history = []      # [(user, bot)]
        random.seed()

    # -------- 文本预处理 --------
    @staticmethod
    def normalize(text: str) -> str:
        text = text.lower().strip()
        # 去掉中英文标点
        zh_punct = "，。！？；：、""''《》（）【】"
        for ch in string.punctuation + zh_punct:
            text = text.replace(ch, " ")
        for k, v in SYNONYMS.items():
            text = text.replace(k, v)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    # -------- 核心匹配 --------
    def reply(self, user_input: str) -> str:
        if not user_input or not user_input.strip():
            return "你想说点什么？"

        norm = self.normalize(user_input)

        for pattern, replies in RULES:
            m = re.search(pattern, norm)
            if not m:
                continue
            template = random.choice(replies)
            answer = self._render(template, m)
            self.history.append((user_input, answer))
            return answer

        # 未命中
        answer = random.choice(DEFAULT_REPLIES)
        self.history.append((user_input, answer))
        return answer

    def _render(self, template: str, match: re.Match) -> str:
        now = datetime.now()
        # 提取人名
        if "{name}" in template:
            groups = [g for g in match.groups() if g]
            if groups:
                self.context["name"] = groups[0].strip()
        return template.format(
            name=self.context.get("name", "朋友"),
            time=now.strftime("%H:%M:%S"),
            date=now.strftime("%Y-%m-%d %A"),
        )


# ==================== Demo ====================

if __name__ == "__main__":
    print("=" * 60)
    print("  简单聊天机器人（规则型） Demo")
    print("=" * 60)

    bot = ChatBot()

    # 模拟对话脚本
    script = [
        "你好！",
        "我叫小明",
        "你是谁？",
        "现在几点？",
        "今天星期几？",
        "讲个笑话",
        "天气怎么样",
        "我今天心情有点难过",
        "1 + 1",
        "谢谢你！",
        "再见",
        "?????",  # 未知输入
    ]

    print("\n--- 自动对话演示 ---")
    for line in script:
        ans = bot.reply(line)
        print(f"  你   > {line}")
        print(f"  Bot  > {ans}\n")

    print(f"  对话轮次: {len(bot.history)}")
    print(f"  记住的变量: {bot.context}")

    # 交互模式（如果想手动测试，去掉下面注释）
    # print("\n--- 进入交互模式（输入 quit 退出） ---")
    # while True:
    #     line = input("你 > ")
    #     if line.strip().lower() in ("quit", "exit"):
    #         break
    #     print("Bot >", bot.reply(line))

    print("=" * 60)
    print("  Demo 运行完毕！")
    print("=" * 60)
