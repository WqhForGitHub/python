# -*- coding: utf-8 -*-
"""
插件系统框架
- 纯 Python 实现的插件框架
- 特性：
  * 自动发现 plugins/ 目录下的插件模块
  * 基于元类的插件注册（继承 Plugin 基类即自动登记）
  * 钩子（Hook）机制：插件可订阅命名事件
  * 插件元数据（name / version / author / description）
  * 启用/禁用 / 列表 / 调用接口
- 提供 demo 主程序，加载内置示例插件并触发钩子。

用法：
    python plugin_system.py
"""
import importlib.util
import os
import sys
from pathlib import Path


# ---------- 插件基础 ----------
class PluginRegistry:
    """全体插件注册表（类级集合）"""
    plugins = {}  # name -> class

    @classmethod
    def register(cls, plugin_cls):
        cls.plugins[plugin_cls.name] = plugin_cls
        return plugin_cls


class PluginMeta(type):
    """元类：定义子类时自动注册"""
    def __init__(cls, name, bases, ns):
        super().__init__(name, bases, ns)
        if bases and getattr(cls, "name", None):
            PluginRegistry.register(cls)


class Plugin(metaclass=PluginMeta):
    """插件基类"""
    name: str = ""
    version: str = "0.1"
    author: str = ""
    description: str = ""

    def __init__(self, app):
        self.app = app
        self.enabled = True

    def on_load(self):
        """加载时调用"""
        pass

    def on_unload(self):
        """卸载时调用"""
        pass


# ---------- 钩子管理 ----------
class HookManager:
    def __init__(self):
        self._hooks = {}  # event -> [(priority, callable)]

    def subscribe(self, event, fn, priority=0):
        self._hooks.setdefault(event, []).append((priority, fn))
        self._hooks[event].sort(key=lambda x: -x[0])

    def emit(self, event, *args, **kwargs):
        results = []
        for _, fn in self._hooks.get(event, []):
            try:
                results.append(fn(*args, **kwargs))
            except Exception as e:
                print(f"[hook:{event}] 异常: {e}")
        return results


# ---------- 应用 / 插件管理 ----------
class App:
    def __init__(self, plugin_dir="plugins"):
        self.plugin_dir = Path(__file__).parent / plugin_dir
        self.hooks = HookManager()
        self.plugins = {}  # name -> 实例

    # ---- 发现 / 加载 ----
    def discover(self):
        if not self.plugin_dir.is_dir():
            self.plugin_dir.mkdir(parents=True, exist_ok=True)
            return
        for py in self.plugin_dir.glob("*.py"):
            if py.name.startswith("_"):
                continue
            self._load_module(py)

    def _load_module(self, path: Path):
        mod_name = f"_plugin_{path.stem}"
        spec = importlib.util.spec_from_file_location(mod_name, path)
        if not spec or not spec.loader:
            return
        module = importlib.util.module_from_spec(spec)
        sys.modules[mod_name] = module
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            print(f"加载失败 {path.name}: {e}")

    def load_all(self):
        """实例化所有已注册插件"""
        for name, cls in PluginRegistry.plugins.items():
            if name in self.plugins:
                continue
            inst = cls(self)
            self.plugins[name] = inst
            inst.on_load()
            print(f"[+] 已加载插件 {name} v{inst.version}")

    def unload(self, name):
        p = self.plugins.pop(name, None)
        if p:
            p.on_unload()
            print(f"[-] 卸载插件 {name}")

    # ---- 控制 ----
    def enable(self, name):
        if name in self.plugins:
            self.plugins[name].enabled = True

    def disable(self, name):
        if name in self.plugins:
            self.plugins[name].enabled = False

    def list_plugins(self):
        for name, p in self.plugins.items():
            mark = "[x]" if p.enabled else "[ ]"
            print(f"  {mark} {name:<15} v{p.version:<6} - {p.description}")

    def emit(self, event, *args, **kwargs):
        return self.hooks.emit(event, *args, **kwargs)


# ---------- 内置示例插件（不依赖外部文件） ----------
class HelloPlugin(Plugin):
    name = "hello"
    version = "1.0"
    author = "demo"
    description = "在启动时打印问候，并响应 greet 事件"

    def on_load(self):
        self.app.hooks.subscribe("startup", self._on_startup)
        self.app.hooks.subscribe("greet", self._on_greet, priority=10)

    def _on_startup(self):
        print(">> hello 插件：欢迎使用！")

    def _on_greet(self, who):
        return f"Hello, {who}!"


class UpperCasePlugin(Plugin):
    name = "uppercase"
    version = "0.5"
    author = "demo"
    description = "将 transform 事件输入转换为大写"

    def on_load(self):
        self.app.hooks.subscribe("transform", self._upper)

    def _upper(self, text):
        return text.upper()


class CounterPlugin(Plugin):
    name = "counter"
    version = "0.2"
    author = "demo"
    description = "统计 transform 事件触发次数"

    def on_load(self):
        self.count = 0
        self.app.hooks.subscribe("transform", self._count, priority=-10)

    def _count(self, text):
        self.count += 1
        return f"[count={self.count}] {text}"


# ---------- demo ----------
def main():
    app = App()
    app.discover()      # 扫描 plugins/ 目录（如有）
    app.load_all()

    print("\n== 已加载插件 ==")
    app.list_plugins()

    print("\n== 触发 startup ==")
    app.emit("startup")

    print("\n== 触发 greet ==")
    for r in app.emit("greet", "World"):
        print("  ->", r)

    print("\n== 触发 transform('hello plugin') ==")
    for r in app.emit("transform", "hello plugin"):
        print("  ->", r)

    print("\n== 禁用 uppercase 后再次 transform ==")
    app.disable("uppercase")
    # 简单忽略禁用的：包装
    def call(event, *a, **kw):
        out = []
        for _, fn in app.hooks._hooks.get(event, []):
            owner = getattr(fn, "__self__", None)
            if owner and not owner.enabled:
                continue
            out.append(fn(*a, **kw))
        return out
    print("  ->", call("transform", "another text"))

    print("\n== 卸载 hello ==")
    app.unload("hello")
    app.list_plugins()


if __name__ == "__main__":
    main()
