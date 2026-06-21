# PyGit —— Python 实现的简化版 Git

纯 Python 标准库实现 Git 的核心模型：内容寻址对象库 + 索引（暂存区） + 引用 + 提交历史。

> 对象格式（blob/tree/commit）与 Git 完全一致，对同一文件计算的 SHA1 与真 git 相同。

## 已实现

| 命令 | 说明 |
|------|------|
| `init` | 初始化 `.pygit/` 目录 |
| `add <file>...` | 把文件写为 blob 并放入索引 |
| `status` | 显示暂存 / 修改 / 未跟踪 |
| `commit -m "msg"` | 把索引构建为 tree，写出 commit |
| `log` | 沿 parent 链回溯打印 |
| `branch [name]` | 列出 / 创建分支 |
| `checkout <name>` | 切换分支或裸 oid（detached HEAD） |
| `diff` | 工作树 vs 索引 的统一 diff |
| `cat-file <oid>` | 输出对象内容（自动识别类型） |
| `ls-tree <oid>` | 列出 tree（接受 commit oid） |
| `demo` | 在临时目录把整个流程跑一遍 |

## 对象格式（与 Git 兼容）

```
blob:    "blob <size>\0<content>"
tree:    "tree <size>\0[<mode> <name>\0<20-byte sha1>]*"
commit:  "commit <size>\0
            tree <sha>
            parent <sha>
            author ...
            committer ...

            <msg>"
```

oid = `sha1(header + body)`，存盘时整体 zlib 压缩，路径 `.pygit/objects/<前2位>/<后38位>`。

## 用法

```bash
mkdir myrepo && cd myrepo
python /path/to/pygit.py init
echo hello > a.txt
python /path/to/pygit.py add a.txt
python /path/to/pygit.py commit -m "first"
python /path/to/pygit.py log
python /path/to/pygit.py branch dev
python /path/to/pygit.py checkout dev
```

或一键演示：

```bash
python pygit.py demo
```

## 设计要点

- **索引**：自定义二进制格式 `[count][name_len][name][20B sha1]*`（比 git 的真实 index 简单）
- **tree 构建**：把扁平 `path -> blob` 映射按 `/` 分组成嵌套 tree
- **HEAD**：`ref: refs/heads/<branch>` 或裸 oid（detached）
- **checkout**：先删除当前已跟踪文件，再按目标 commit 的 tree 写入
- **diff**：使用标准库 `difflib.unified_diff`
