# 插件系统框架

纯 Python 实现的轻量级插件框架。

## 特性
- 元类自动注册：继承 `Plugin` 即登记到 `PluginRegistry`
- 钩子机制：`hooks.subscribe(event, fn, priority)` / `app.emit(event, ...)`
- 自动发现 `plugins/` 目录下的模块
- 插件元数据（name, version, author, description）
- 启用 / 禁用 / 卸载 / 列表

## 用法
```bash
python plugin_system.py
```

可在 `plugins/` 目录新建 `.py` 文件，继承 `Plugin` 即被自动加载：

```python
from plugin_system import Plugin

class MyPlugin(Plugin):
    name = "myplugin"
    version = "0.1"
    description = "示例"

    def on_load(self):
        self.app.hooks.subscribe("startup", lambda: print("hi"))
```
