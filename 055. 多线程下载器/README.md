# 55. 多线程下载器

纯标准库（urllib + threading）实现的多线程 HTTP 下载器。

## 特性
- HEAD 探测文件大小与 Range 支持
- 支持 Range 时自动分段并发下载
- 不支持 Range 时回退单线程
- 实时进度条 / 速度显示

## 用法
```
python downloader.py https://example.com/file.zip -o file.zip -n 8
```
