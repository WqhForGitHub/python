# 配置管理系统

纯 Python 实现，无第三方依赖。

## 特性
- 支持 `.json / .ini / .env / .yml`（极简 YAML）格式
- 多源合并：默认值 < 文件 < 环境变量 < 命令行 `--key=value`
- 路径访问：`cfg.get("db.host")`、`cfg["db.port"]`
- 类型转换：`as_int / as_bool / as_list`
- 变量插值：`"Hello, ${app.name}!"`
- 变更监听：`on_change(callback)`

## 用法
```python
from config import Config
cfg = Config(defaults={"app": {"debug": False}})
cfg.load_file("config.json").load_env(prefix="APP_").load_argv()
print(cfg.get("db.host"))
```

运行 demo：
```bash
python config.py --db.port=6543
```
