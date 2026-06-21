# 日志框架（类似 logging 扩展）

纯 Python 实现的日志框架，不依赖标准库 `logging`。

## 特性
- 等级：`DEBUG / INFO / WARNING / ERROR / CRITICAL`
- Handler：`StreamHandler` / `FileHandler` / `RotatingFileHandler`
- Formatter：`%(time)s %(level)s %(name)s %(message)s` 等
- Filter：函数式过滤
- 层级 Logger：`get_logger("app.db")` 自动继承父级
- 彩色控制台输出（可关）
- `extra` 字段注入

## 用法
```python
from logger import get_logger, FileHandler

log = get_logger("app")
log.set_level("DEBUG")
log.add_handler(FileHandler("logs/app.log"))

log.info("hello %s", "world")
```

运行 demo：
```bash
python logger.py
```
