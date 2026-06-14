# PyDocker —— Python 实现的 Docker 模拟版

纯标准库实现，模拟 Docker 的核心概念与命令行用法，**不**做真正的 Linux namespace/cgroups 隔离。

## 核心概念映射

| 真 Docker | 本模拟版 |
| --- | --- |
| 镜像层 (overlayfs) | `~/.pydocker/images/<sha256>/` 目录 |
| 容器可写层 | `~/.pydocker/containers/<cid>/rootfs/` 目录（启动时 copy-on-write 拷贝镜像） |
| `docker.sock` 元数据 | `~/.pydocker/meta.json` |
| namespace 进程隔离 | `subprocess` + `cwd` 切换 + 受限环境变量 |

## 命令

```bash
python pydocker.py build -t myapp ./app          # 解析 Dockerfile 构建镜像
python pydocker.py images
python pydocker.py run -d --name web myapp       # 后台运行
python pydocker.py run myapp echo hello          # 一次性运行（前台）
python pydocker.py ps [-a]
python pydocker.py logs [-f] web
python pydocker.py exec web ls /
python pydocker.py stop web
python pydocker.py rm [-f] web
python pydocker.py rmi myapp
python pydocker.py commit web mynewimage
python pydocker.py demo                          # 一键自测
```

## 支持的 Dockerfile 指令

`FROM` `COPY` `RUN` `CMD` `ENV` `WORKDIR`

## 设计要点

1. **镜像 = 目录**：`build` 时按 Dockerfile 一条条执行，把文件落到镜像层。`RUN` 直接在该目录里 `subprocess.run` 一次。
2. **容器 = 拷贝**：`run` 时 `shutil.copytree` 把镜像层拷到容器目录，模拟 OverlayFS 的可写层（最朴素的 CoW）。
3. **进程 = subprocess**：`detach` 时把 stdout/stderr 重定向到容器日志文件，前台模式则实时 stream。
4. **`commit`**：直接把容器当前可写层再拷一份，注册成新镜像。
5. **`ps`**：每次都通过 PID 检查后台容器是否仍存活，自动把僵尸标成 `exited`。

## 为何不能做强隔离

真 Docker 依赖 `clone(CLONE_NEWPID|CLONE_NEWNS|...)`、`pivot_root`、`cgroups`，这些纯 Python 标准库都拿不到（且 Windows 完全没有）。本项目目的是用 ~600 行代码把 **「镜像-容器-命令」三层抽象** 与 docker CLI 的体验讲清楚。
