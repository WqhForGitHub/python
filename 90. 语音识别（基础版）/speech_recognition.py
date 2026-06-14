"""
语音识别（基础版）- 纯 Python 实现
=====================================
仅使用标准库 wave + math，对 WAV 音频做：
1. 读取 PCM 音频
2. 分帧 + 加窗（Hamming）
3. 预加重
4. FFT（Cooley-Tukey 实现，无 numpy）
5. 提取频率特征 / 简单的 DTW 模板匹配识别孤立词

注意：纯 Python 实现速度较慢，仅作教学/原型演示。
本模块还提供：
- 一个简单的合成器 synth_tone()：生成 WAV 测试音
- 一个最小的孤立词识别器 SimpleRecognizer
"""

import math
import wave
import struct
import os
import cmath


# ---------- 基础 DSP ----------
def read_wav(path):
    """读取 PCM WAV，返回 (samples, sample_rate)"""
    with wave.open(path, "rb") as w:
        n = w.getnframes()
        sr = w.getframerate()
        ch = w.getnchannels()
        sw = w.getsampwidth()
        raw = w.readframes(n)
    fmt = {1: "b", 2: "h", 4: "i"}[sw]
    samples = list(struct.unpack(f"<{n*ch}{fmt}", raw))
    if ch == 2:  # 立体声 -> 单声道
        samples = [(samples[i] + samples[i + 1]) // 2 for i in range(0, len(samples), 2)]
    # 归一化到 [-1, 1]
    max_v = float(2 ** (8 * sw - 1))
    samples = [s / max_v for s in samples]
    return samples, sr


def write_wav(path, samples, sr=16000):
    """写入 16-bit PCM WAV"""
    data = b"".join(struct.pack("<h", max(-32768, min(32767, int(s * 32767)))) for s in samples)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(data)


def pre_emphasis(samples, alpha=0.97):
    """预加重，提升高频"""
    out = [samples[0]]
    for i in range(1, len(samples)):
        out.append(samples[i] - alpha * samples[i - 1])
    return out


def hamming(n):
    return [0.54 - 0.46 * math.cos(2 * math.pi * i / (n - 1)) for i in range(n)]


def frame_signal(samples, frame_len, frame_shift):
    """将信号切分为重叠帧"""
    frames = []
    i = 0
    while i + frame_len <= len(samples):
        frames.append(samples[i:i + frame_len])
        i += frame_shift
    return frames


def fft(x):
    """递归 FFT (Cooley-Tukey)。x 长度需为 2 的幂。"""
    n = len(x)
    if n == 1:
        return list(x)
    if n & (n - 1):
        # 补零到下一个 2 的幂
        m = 1
        while m < n:
            m <<= 1
        x = list(x) + [0.0] * (m - n)
        n = m
    even = fft(x[0::2])
    odd = fft(x[1::2])
    result = [0] * n
    for k in range(n // 2):
        t = cmath.exp(-2j * math.pi * k / n) * odd[k]
        result[k] = even[k] + t
        result[k + n // 2] = even[k] - t
    return result


def magnitude_spectrum(frame):
    """单帧的幅度谱"""
    spec = fft(frame)
    half = len(spec) // 2
    return [abs(c) for c in spec[:half]]


def feature_vector(samples, sr, frame_ms=25, shift_ms=10, n_bins=16):
    """提取每帧的频带能量作为特征序列"""
    samples = pre_emphasis(samples)
    frame_len = int(sr * frame_ms / 1000)
    frame_shift = int(sr * shift_ms / 1000)
    win = hamming(frame_len)

    feats = []
    for fr in frame_signal(samples, frame_len, frame_shift):
        wf = [s * w for s, w in zip(fr, win)]
        spec = magnitude_spectrum(wf)
        # 划分 n_bins 个频带，求每个频带的对数能量
        size = max(1, len(spec) // n_bins)
        vec = []
        for b in range(n_bins):
            chunk = spec[b * size:(b + 1) * size]
            energy = sum(c * c for c in chunk) / max(1, len(chunk))
            vec.append(math.log(energy + 1e-10))
        feats.append(vec)
    return feats


# ---------- DTW ----------
def dtw_distance(a, b):
    """计算两个特征序列的 DTW 距离"""
    n, m = len(a), len(b)
    if n == 0 or m == 0:
        return float("inf")
    INF = float("inf")
    dp = [[INF] * (m + 1) for _ in range(n + 1)]
    dp[0][0] = 0
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = math.sqrt(sum((a[i - 1][k] - b[j - 1][k]) ** 2 for k in range(len(a[0]))))
            dp[i][j] = cost + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])
    return dp[n][m] / (n + m)


# ---------- 简单的孤立词识别 ----------
class SimpleRecognizer:
    def __init__(self):
        self.templates = {}  # word -> feature_vector

    def enroll(self, word, samples, sr):
        self.templates[word] = feature_vector(samples, sr)

    def recognize(self, samples, sr):
        feats = feature_vector(samples, sr)
        best, best_d = None, float("inf")
        for word, tpl in self.templates.items():
            d = dtw_distance(feats, tpl)
            if d < best_d:
                best, best_d = word, d
        return best, best_d


# ---------- 合成测试音 ----------
def synth_tone(freq, duration=0.5, sr=16000, amp=0.5):
    """生成正弦波，用于演示识别"""
    n = int(sr * duration)
    return [amp * math.sin(2 * math.pi * freq * i / sr) for i in range(n)]


def demo():
    print("=" * 50)
    print("语音识别（基础版）演示")
    print("使用纯 Python 合成不同频率的正弦音作为'词汇'，")
    print("再用 DTW 模板匹配识别。\n")

    sr = 8000  # 用低采样率加快纯 Python 计算
    rec = SimpleRecognizer()

    # 注册三个'词'：低频、中频、高频
    rec.enroll("低音", synth_tone(220, 0.4, sr), sr)
    rec.enroll("中音", synth_tone(550, 0.4, sr), sr)
    rec.enroll("高音", synth_tone(1100, 0.4, sr), sr)
    print("已注册模板：低音(220Hz) / 中音(550Hz) / 高音(1100Hz)\n")

    tests = [
        ("应为 低音", synth_tone(230, 0.4, sr)),
        ("应为 中音", synth_tone(540, 0.4, sr)),
        ("应为 高音", synth_tone(1080, 0.4, sr)),
    ]
    for label, sig in tests:
        word, d = rec.recognize(sig, sr)
        print(f"[{label}] -> 识别结果: {word}  (DTW距离={d:.3f})")

    # 演示 WAV 写入
    out_path = "demo_tone.wav"
    write_wav(out_path, synth_tone(440, 1.0, sr), sr)
    print(f"\n已保存示例 WAV: {out_path}")
    if os.path.exists(out_path):
        os.remove(out_path)
        print("(演示完毕，文件已清理)")
    print("=" * 50)


if __name__ == "__main__":
    demo()
