# -*- coding: utf-8 -*-
"""
命令行 Shell（仿 bash）
- 纯 Python 实现的简易交互式 Shell
- 内建命令：cd / pwd / ls / cat / echo / export / unset / env / history /
           help / exit / clear / mkdir / rm / touch / which
- 支持：环境变量展开 ($VAR / ${VAR})、~ 展开、引号、简单管道 a | b、
        输出重定向 >  >>，输入重定向 <
- 支持：执行外部程序（通过 subprocess）
- 历史记录：保存到 ~/.pyshell_history

用法：
    python shell.py
"""
import os
import sys
import shlex
import subprocess
from pathlib import Path


HISTORY_FILE = Path.home() / ".pyshell_history"


# ---------- 词法 ----------
def expand(token: str, env: dict) -> str:
    """展开 ~ 和 $VAR / ${VAR}"""
    if token.startswith("~"):
        token = str(Path.home()) + token[1:]
    out = []
    i = 0
    while i < len(token):
        c = token[i]
        if c == "$":
            i += 1
            if i < len(token) and token[i] == "{":
                j = token.find("}", i)
                if j < 0:
                    out.append("${"); i += 1; continue
                name = token[i + 1:j]
                out.append(env.get(name, ""))
                i = j + 1
            else:
                j = i
                while j < len(token) and (token[j].isalnum() or token[j] == "_"):
                    j += 1
                name = token[i:j]
                out.append(env.get(name, ""))
                i = j
        else:
            out.append(c)
            i += 1
    return "".join(out)


def parse_line(line: str, env: dict):
    """切分管道，再对每段切分 token 并提取重定向"""
    try:
        parts = shlex.split(line, posix=True)
    except ValueError as e:
        raise ValueError(f"语法错误: {e}")

    parts = [expand(p, env) for p in parts]

    # 按管道符 | 分段
    segments = []
    cur = []
    for p in parts:
        if p == "|":
            if not cur:
                raise ValueError("语法错误: 管道为空")
            segments.append(cur)
            cur = []
        else:
            cur.append(p)
    if not cur:
        raise ValueError("语法错误: 管道末端为空")
    segments.append(cur)

    # 提取重定向
    cmds = []
    for seg in segments:
        argv = []
        in_file = None
        out_file = None
        out_append = False
        i = 0
        while i < len(seg):
            t = seg[i]
            if t == ">":
                out_file = seg[i + 1]; out_append = False; i += 2
            elif t == ">>":
                out_file = seg[i + 1]; out_append = True; i += 2
            elif t == "<":
                in_file = seg[i + 1]; i += 2
            else:
                argv.append(t); i += 1
        if not argv:
            raise ValueError("语法错误: 命令为空")
        cmds.append({"argv": argv, "in": in_file, "out": out_file, "append": out_append})
    return cmds


# ---------- 内建命令 ----------
class Shell:
    def __init__(self):
        self.env = dict(os.environ)
        self.history = []
        self._load_history()
        self.builtins = {
            "cd": self.cmd_cd, "pwd": self.cmd_pwd, "exit": self.cmd_exit,
            "echo": self.cmd_echo, "export": self.cmd_export, "unset": self.cmd_unset,
            "env": self.cmd_env, "ls": self.cmd_ls, "cat": self.cmd_cat,
            "history": self.cmd_history, "help": self.cmd_help, "clear": self.cmd_clear,
            "mkdir": self.cmd_mkdir, "rm": self.cmd_rm, "touch": self.cmd_touch,
            "which": self.cmd_which,
        }

    # ---- 历史 ----
    def _load_history(self):
        if HISTORY_FILE.exists():
            try:
                self.history = HISTORY_FILE.read_text(encoding="utf-8").splitlines()
            except Exception:
                self.history = []

    def _save_history(self):
        try:
            HISTORY_FILE.write_text("\n".join(self.history[-1000:]), encoding="utf-8")
        except Exception:
            pass

    # ---- 内建实现 ----
    def cmd_cd(self, argv, stdin, stdout):
        target = argv[1] if len(argv) > 1 else str(Path.home())
        try:
            os.chdir(target)
            return 0
        except Exception as e:
            stdout.write(f"cd: {e}\n"); return 1

    def cmd_pwd(self, argv, stdin, stdout):
        stdout.write(os.getcwd() + "\n"); return 0

    def cmd_exit(self, argv, stdin, stdout):
        code = int(argv[1]) if len(argv) > 1 else 0
        self._save_history()
        sys.exit(code)

    def cmd_echo(self, argv, stdin, stdout):
        stdout.write(" ".join(argv[1:]) + "\n"); return 0

    def cmd_export(self, argv, stdin, stdout):
        for kv in argv[1:]:
            if "=" in kv:
                k, v = kv.split("=", 1)
                self.env[k] = v
                os.environ[k] = v
            else:
                stdout.write(f"{kv}={self.env.get(kv, '')}\n")
        return 0

    def cmd_unset(self, argv, stdin, stdout):
        for k in argv[1:]:
            self.env.pop(k, None)
            os.environ.pop(k, None)
        return 0

    def cmd_env(self, argv, stdin, stdout):
        for k, v in sorted(self.env.items()):
            stdout.write(f"{k}={v}\n")
        return 0

    def cmd_ls(self, argv, stdin, stdout):
        path = argv[1] if len(argv) > 1 else "."
        try:
            for name in sorted(os.listdir(path)):
                stdout.write(name + "\n")
            return 0
        except Exception as e:
            stdout.write(f"ls: {e}\n"); return 1

    def cmd_cat(self, argv, stdin, stdout):
        if len(argv) == 1:
            stdout.write(stdin.read()); return 0
        for f in argv[1:]:
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    stdout.write(fp.read())
            except Exception as e:
                stdout.write(f"cat: {f}: {e}\n"); return 1
        return 0

    def cmd_history(self, argv, stdin, stdout):
        for i, h in enumerate(self.history, 1):
            stdout.write(f"{i:>4}  {h}\n")
        return 0

    def cmd_help(self, argv, stdin, stdout):
        stdout.write("内建命令：" + ", ".join(sorted(self.builtins)) + "\n")
        stdout.write("支持：管道 | 、重定向 > >> < 、变量 $VAR、~ 展开\n")
        return 0

    def cmd_clear(self, argv, stdin, stdout):
        os.system("cls" if os.name == "nt" else "clear"); return 0

    def cmd_mkdir(self, argv, stdin, stdout):
        for d in argv[1:]:
            try:
                os.makedirs(d, exist_ok=True)
            except Exception as e:
                stdout.write(f"mkdir: {e}\n"); return 1
        return 0

    def cmd_rm(self, argv, stdin, stdout):
        recursive = "-r" in argv or "-rf" in argv
        targets = [a for a in argv[1:] if not a.startswith("-")]
        for t in targets:
            try:
                if os.path.isdir(t):
                    if recursive:
                        import shutil
                        shutil.rmtree(t)
                    else:
                        stdout.write(f"rm: {t}: 是目录\n"); return 1
                else:
                    os.remove(t)
            except Exception as e:
                stdout.write(f"rm: {e}\n"); return 1
        return 0

    def cmd_touch(self, argv, stdin, stdout):
        for f in argv[1:]:
            try:
                Path(f).touch()
            except Exception as e:
                stdout.write(f"touch: {e}\n"); return 1
        return 0

    def cmd_which(self, argv, stdin, stdout):
        for name in argv[1:]:
            if name in self.builtins:
                stdout.write(f"{name}: 内建命令\n"); continue
            paths = self.env.get("PATH", os.defpath).split(os.pathsep)
            found = None
            for p in paths:
                cand = os.path.join(p, name)
                if os.path.isfile(cand):
                    found = cand; break
                if os.name == "nt":
                    for ext in (".exe", ".bat", ".cmd"):
                        if os.path.isfile(cand + ext):
                            found = cand + ext; break
                    if found: break
            stdout.write((found or f"{name}: 未找到") + "\n")
        return 0

    # ---- 执行 ----
    def execute(self, line: str):
        line = line.strip()
        if not line:
            return
        if line.startswith("#"):
            return
        self.history.append(line)
        try:
            cmds = parse_line(line, self.env)
        except ValueError as e:
            print(e); return

        # 单命令优化（含内建）
        if len(cmds) == 1:
            self._run_single(cmds[0])
        else:
            self._run_pipeline(cmds)

    def _open_in(self, path):
        return open(path, "r", encoding="utf-8") if path else None

    def _open_out(self, path, append):
        if not path: return None
        return open(path, "a" if append else "w", encoding="utf-8")

    def _run_single(self, cmd):
        argv = cmd["argv"]
        stdin = self._open_in(cmd["in"]) or sys.stdin
        stdout = self._open_out(cmd["out"], cmd["append"]) or sys.stdout
        try:
            if argv[0] in self.builtins:
                self.builtins[argv[0]](argv, stdin, stdout)
            else:
                # 外部命令
                try:
                    proc = subprocess.run(
                        argv,
                        stdin=stdin if cmd["in"] else None,
                        stdout=stdout if cmd["out"] else None,
                        env=self.env,
                    )
                    if proc.returncode != 0 and not cmd["out"]:
                        pass
                except FileNotFoundError:
                    print(f"{argv[0]}: 命令未找到")
        finally:
            if cmd["in"]: stdin.close()
            if cmd["out"]: stdout.close()

    def _run_pipeline(self, cmds):
        """简易管道：前面命令产物作为字符串传给后面"""
        import io
        prev_out = ""
        if cmds[0]["in"]:
            with open(cmds[0]["in"], "r", encoding="utf-8") as f:
                prev_out = f.read()

        for idx, cmd in enumerate(cmds):
            argv = cmd["argv"]
            stdin = io.StringIO(prev_out)
            stdout = io.StringIO()
            if argv[0] in self.builtins:
                self.builtins[argv[0]](argv, stdin, stdout)
                prev_out = stdout.getvalue()
            else:
                try:
                    proc = subprocess.run(
                        argv, input=prev_out, capture_output=True,
                        text=True, env=self.env
                    )
                    prev_out = proc.stdout
                except FileNotFoundError:
                    print(f"{argv[0]}: 命令未找到"); return

        # 末端输出
        last = cmds[-1]
        if last["out"]:
            mode = "a" if last["append"] else "w"
            with open(last["out"], mode, encoding="utf-8") as f:
                f.write(prev_out)
        else:
            sys.stdout.write(prev_out)

    # ---- 主循环 ----
    def repl(self):
        print("PyShell 0.1 — 输入 help 查看帮助，exit 退出")
        while True:
            try:
                cwd = os.getcwd()
                prompt = f"\n[pysh {os.path.basename(cwd) or cwd}]$ "
                line = input(prompt)
            except EOFError:
                print(); break
            except KeyboardInterrupt:
                print(); continue
            self.execute(line)
        self._save_history()


def main():
    sh = Shell()
    if len(sys.argv) > 1:
        # 脚本模式
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            for line in f:
                sh.execute(line)
    else:
        sh.repl()


if __name__ == "__main__":
    main()
