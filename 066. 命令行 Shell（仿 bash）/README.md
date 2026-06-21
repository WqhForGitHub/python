# 命令行 Shell（仿 bash）

纯 Python 实现的简易交互式 Shell。

## 功能
- 内建命令：`cd`, `pwd`, `ls`, `cat`, `echo`, `export`, `unset`, `env`, `history`, `help`, `exit`, `clear`, `mkdir`, `rm`, `touch`, `which`
- 调用外部程序（通过 `subprocess`）
- 简单管道 `a | b`
- 输出重定向 `>` / `>>`，输入重定向 `<`
- 环境变量展开 `$VAR` / `${VAR}`
- `~` 展开为 home 目录
- 历史记录持久化到 `~/.pyshell_history`

## 用法
```bash
python shell.py            # 进入交互
python shell.py script.sh  # 执行脚本
```

## 示例
```
[pysh demo]$ echo Hello $USER
[pysh demo]$ ls | cat > files.txt
[pysh demo]$ export NAME=World
[pysh demo]$ echo "Hi, $NAME"
```
