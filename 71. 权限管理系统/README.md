# Web 服务器（纯 socket 实现）

> 注：根据用户指示，本 demo 放置在「71. 权限管理系统」目录下。

完全基于 `socket` 与 `threading`，不使用 `http.server`、`wsgiref` 等高层模块。

## 特性
- HTTP/1.1：`GET / POST / HEAD / OPTIONS`
- 静态文件服务（自动 MIME）
- 路由装饰器：`@app.route("/path", methods=["GET"])`
- 路径参数：`/user/<id>`
- 多线程并发
- 简易模板（`{{ name }}` 替换）

## 用法
```bash
python web_server.py
# 访问 http://localhost:8000
```
