# 57. Web 服务器（纯 socket 实现）

完全基于 socket 的 Web 框架（无 http.server / wsgi）。

## 特性
- 路由装饰器 `@app.route("/path/<var>", methods=("GET","POST"))`
- 路径参数、查询字符串、URL 编码表单解析
- 极简模板渲染（`{{var}}` 替换）
- 多线程并发

## 运行
```
python web_server.py
```
访问 http://127.0.0.1:8080
