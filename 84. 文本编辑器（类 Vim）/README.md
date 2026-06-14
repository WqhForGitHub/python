# PyVim —— 纯 Python 标准库实现的 Vim 风格终端文本编辑器

仅依赖标准库 `curses`（Linux/macOS 自带；Windows 需 `pip install windows-curses`）。

## 用法

```bash
python pyvim.py [文件名]
```

## 已实现的 Vim 特性

### 模式
- `NORMAL`（默认） / `INSERT` / `VISUAL` / `COMMAND`
- `Esc` 回到 NORMAL，`i / a / I / A / o / O` 进入 INSERT
- `v` 进入 VISUAL
- `:` 进入 COMMAND

### 移动（NORMAL/VISUAL）
| 键 | 作用 |
| --- | --- |
| `h j k l` | 左下上右 |
| `w / b / e` | 单词前进 / 后退 / 单词末尾 |
| `0 / $` | 行首 / 行尾 |
| `gg / G` | 文件首 / 文件尾 |
| `Ctrl-d / Ctrl-u` | 半页下/上 |

### 编辑
| 键 | 作用 |
| --- | --- |
| `i a I A o O` | 插入位置选项 |
| `x` | 删字符 |
| `dd / dw` | 删行 / 删词 |
| `yy / y`(visual) | 复制行 / 复制选区 |
| `p P` | 粘贴 |
| `u / Ctrl-r` | 撤销 / 重做 |

### 搜索 & 替换
| 命令 | 作用 |
| --- | --- |
| `/pattern` | 正则搜索（实时高亮所有命中） |
| `n / N` | 下/上一个匹配 |
| `:%s/pat/rep/g` | 全局替换（regex） |

### Ex 命令（`:` 后）
- `:w [name]` `:q` `:q!` `:wq` `:x`
- `:e file` 打开新文件
- `:set number` / `:set nonumber`
- `:NNN` 跳到第 NNN 行

## 设计要点

- 单文件 ~600 行，只用标准库
- **撤销栈**：每次修改前 `deepcopy(lines)` 入栈；`u` 弹栈到 redo 栈
- **搜索高亮**：`re.finditer` 全文扫描，绘制阶段套黄底
- **可视模式**：用「锚点 + 光标」一对坐标；选区按行渲染、`y/d` 时再做范围切割
- **滚动**：根据光标位置自动调整 `top / left`，支持横向卷动
- **颜色对**：`curses.init_pair` 定义 4 套：搜索高亮 / 状态栏 / 行号 / 可视选区

## 已知限制

- 不支持寄存器 (`"a` 之类)、宏 (`q`)、多缓冲区
- 替换不支持交互式 `c` 标记
- 不渲染语法高亮（这是个 ~600 行的玩具）
