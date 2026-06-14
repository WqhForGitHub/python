"""
图像识别（纯 Python + 基础算法）
=====================================
不依赖 numpy / opencv，仅用标准库 + math 实现：
- PGM (P5 二值/灰度图) 读写
- 灰度化、阈值化、卷积、Sobel 边缘检测
- 简单数字 KNN 识别（基于像素特征）

数据：内置一组 5x5 数字字模（0-9 简化点阵），
通过最近邻匹配识别测试样本。
"""

import math
import os
import struct
from collections import Counter


# ---------- 图像 IO（PGM 二进制 P5） ----------
def write_pgm(path, pixels, width, height, max_val=255):
    """将像素一维 list 写为 PGM"""
    header = f"P5\n{width} {height}\n{max_val}\n".encode("ascii")
    body = bytes(max(0, min(max_val, int(p))) for p in pixels)
    with open(path, "wb") as f:
        f.write(header + body)


def read_pgm(path):
    with open(path, "rb") as f:
        magic = f.readline().strip()
        if magic != b"P5":
            raise ValueError("仅支持 P5 PGM")
        # 跳过注释
        line = f.readline()
        while line.startswith(b"#"):
            line = f.readline()
        w, h = map(int, line.split())
        max_val = int(f.readline().strip())
        body = f.read()
    return list(body), w, h


# ---------- 基础图像处理 ----------
def to_grayscale(rgb_pixels, width, height):
    """rgb_pixels 是 (r,g,b) 列表，返回灰度一维数组"""
    return [int(0.299 * r + 0.587 * g + 0.114 * b) for r, g, b in rgb_pixels]


def threshold(pixels, t=128):
    return [255 if p >= t else 0 for p in pixels]


def conv2d(pixels, w, h, kernel):
    """二维卷积，kernel 是奇数边长方阵"""
    k = len(kernel)
    pad = k // 2
    out = [0] * (w * h)
    for y in range(h):
        for x in range(w):
            acc = 0.0
            for ky in range(k):
                for kx in range(k):
                    yy = min(h - 1, max(0, y + ky - pad))
                    xx = min(w - 1, max(0, x + kx - pad))
                    acc += pixels[yy * w + xx] * kernel[ky][kx]
            out[y * w + x] = acc
    return out


def sobel(pixels, w, h):
    """Sobel 边缘检测，返回梯度幅值（0-255）"""
    kx = [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]
    ky = [[-1, -2, -1], [0, 0, 0], [1, 2, 1]]
    gx = conv2d(pixels, w, h, kx)
    gy = conv2d(pixels, w, h, ky)
    mag = [math.sqrt(a * a + b * b) for a, b in zip(gx, gy)]
    m = max(mag) or 1
    return [int(v / m * 255) for v in mag]


def resize(pixels, w, h, new_w, new_h):
    """最近邻缩放"""
    out = [0] * (new_w * new_h)
    for y in range(new_h):
        for x in range(new_w):
            src_x = int(x * w / new_w)
            src_y = int(y * h / new_h)
            out[y * new_w + x] = pixels[src_y * w + src_x]
    return out


# ---------- 简单 KNN 数字识别 ----------
DIGIT_TEMPLATES_5x5 = {
    "0": [
        "01110",
        "10001",
        "10001",
        "10001",
        "01110",
    ],
    "1": [
        "00100",
        "01100",
        "00100",
        "00100",
        "01110",
    ],
    "2": [
        "01110",
        "10001",
        "00010",
        "00100",
        "11111",
    ],
    "3": [
        "11110",
        "00001",
        "01110",
        "00001",
        "11110",
    ],
    "4": [
        "00010",
        "00110",
        "01010",
        "11111",
        "00010",
    ],
    "5": [
        "11111",
        "10000",
        "11110",
        "00001",
        "11110",
    ],
    "6": [
        "01110",
        "10000",
        "11110",
        "10001",
        "01110",
    ],
    "7": [
        "11111",
        "00001",
        "00010",
        "00100",
        "01000",
    ],
    "8": [
        "01110",
        "10001",
        "01110",
        "10001",
        "01110",
    ],
    "9": [
        "01110",
        "10001",
        "01111",
        "00001",
        "01110",
    ],
}


def template_to_vec(rows):
    return [1.0 if c == "1" else 0.0 for r in rows for c in r]


def euclid(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


class DigitKNN:
    def __init__(self, k=1):
        self.k = k
        self.samples = []
        for label, rows in DIGIT_TEMPLATES_5x5.items():
            self.samples.append((label, template_to_vec(rows)))

    def add_sample(self, label, vec):
        self.samples.append((label, vec))

    def predict(self, vec):
        dists = [(label, euclid(vec, s)) for label, s in self.samples]
        dists.sort(key=lambda x: x[1])
        topk = [lbl for lbl, _ in dists[:self.k]]
        return Counter(topk).most_common(1)[0][0]


def add_noise(rows, flip_prob=0.1, seed=42):
    """随机翻转一些点用于测试鲁棒性"""
    import random
    random.seed(seed)
    out = []
    for r in rows:
        new_r = ""
        for c in r:
            if random.random() < flip_prob:
                new_r += "0" if c == "1" else "1"
            else:
                new_r += c
        out.append(new_r)
    return out


def print_digit(rows):
    for r in rows:
        print(r.replace("1", "█").replace("0", " "))


def demo():
    print("=" * 50)
    print("【图像识别 Demo】")
    print()
    print("--- 边缘检测 (Sobel) ---")
    # 构造一张 16x16 含矩形的图
    w = h = 16
    img = [0] * (w * h)
    for y in range(4, 12):
        for x in range(4, 12):
            img[y * w + x] = 200
    edges = sobel(img, w, h)
    print("原图 (5+ 表示像素值)：")
    for y in range(h):
        row = ""
        for x in range(w):
            row += "#" if img[y * w + x] > 100 else "."
        print(row)
    print("\n边缘图：")
    for y in range(h):
        row = ""
        for x in range(w):
            row += "#" if edges[y * w + x] > 80 else "."
        print(row)

    print("\n--- 数字识别 (KNN, k=1) ---")
    knn = DigitKNN(k=1)
    test_digits = ["3", "7", "8", "5"]
    for d in test_digits:
        noisy = add_noise(DIGIT_TEMPLATES_5x5[d], flip_prob=0.1, seed=hash(d) & 0xFFFF)
        print(f"\n带噪声数字 (真实: {d}):")
        print_digit(noisy)
        pred = knn.predict(template_to_vec(noisy))
        print(f"识别结果: {pred}")

    # 写一张 PGM 演示
    out = "demo_edges.pgm"
    write_pgm(out, edges, w, h)
    if os.path.exists(out):
        size = os.path.getsize(out)
        print(f"\n已保存 PGM: {out} ({size} bytes)")
        os.remove(out)
        print("(演示完毕，文件已清理)")
    print("=" * 50)


if __name__ == "__main__":
    demo()
