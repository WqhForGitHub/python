# 多阶段构建：减小镜像体积
FROM python:3.11-slim AS builder

WORKDIR /app

# 系统依赖（asyncpg / bcrypt 编译）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ------------------------------------------------------------
FROM python:3.11-slim

WORKDIR /app

# 运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# 拷贝已安装的依赖
COPY --from=builder /install /usr/local

# 拷贝应用代码
COPY . .

# 非 root 用户运行
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# 生产启动：多 worker + proxy 头
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--proxy-headers", "--forwarded-allow-ips=*"]
