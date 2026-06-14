"""
分布式任务队列 - 任务函数注册表

Worker 通过函数名（字符串）查找实际执行函数。
将任务函数集中注册在此，便于扩展。
"""

import time


def add(a, b):
    """加法（演示用）"""
    return a + b


def multiply(a, b):
    """乘法"""
    return a * b


def slow_square(n):
    """模拟耗时任务：求平方"""
    time.sleep(1)
    return n * n


def factorial(n):
    """阶乘"""
    if n < 0:
        raise ValueError("n 必须 >= 0")
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result


def reverse_str(s):
    """字符串反转"""
    return s[::-1]


# 任务注册表：函数名 -> 函数对象
TASK_REGISTRY = {
    "add": add,
    "multiply": multiply,
    "slow_square": slow_square,
    "factorial": factorial,
    "reverse_str": reverse_str,
}


def execute(func_name: str, args: list):
    """根据函数名执行任务"""
    if func_name not in TASK_REGISTRY:
        raise ValueError(f"未注册的任务函数: {func_name}")
    return TASK_REGISTRY[func_name](*args)
