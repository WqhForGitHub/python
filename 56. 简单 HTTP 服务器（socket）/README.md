# 56. 简单 HTTP 服务器（socket）

完全基于 socket 解析 HTTP 请求并响应的简单服务器。

## 特性
- 仅 GET 方法
- 静态文件服务、目录浏览、自动 index.html
- 多线程处理连接
- 防止路径穿越

## 运行
```
python http_server.py --host 127.0.0.1 --port 8000 --root .
```
打开浏览器访问 http://127.0.0.1:8000
