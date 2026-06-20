# 06. 文件上传下载系统 (FastAPI Demo)

基于 FastAPI 的文件上传下载系统 Demo，支持 **图片 / 文档上传**、**本地 / MinIO 对象存储**、**文件权限控制（public / private / shared）**。

## 功能特性

| 模块 | 说明 |
| --- | --- |
| 文件上传 / 下载 | 图片、文档等，支持原始文件名下载 |
| 存储后端可切换 | 本地文件系统（默认）/ MinIO（S3 兼容），统一接口 |
| 权限控制 | public（公开）/ private（仅 owner）/ shared（owner + 授权用户） |
| 共享授权 | owner 可将文件共享给指定用户，自动切换为 shared |
| 安全防护 | 扩展名白名单、大小限制、目录穿越防护、sha256 校验 |
| 存储降级 | MinIO 不可用时自动降级为本地存储 |

## 项目结构

```
06.文件上传下载系统/
├── main.py                # 应用入口 + 示例数据
├── config.py              # 配置（存储后端 / MinIO / 上传限制）
├── database.py            # 引擎 / Session
├── models.py              # ORM 模型 (User / FileRecord / FileShare)
├── schemas.py             # Pydantic 模型
├── storage.py             # 存储后端抽象（Local / MinIO）
├── deps.py                # 依赖项（当前用户 / 权限判断）
├── crud/
│   ├── __init__.py
│   └── file.py            # 文件 CRUD + 共享授权
├── routers/
│   ├── __init__.py
│   └── files.py           # 上传 / 下载 / 权限 / 共享
├── uploads/               # 本地存储目录（运行时生成）
├── requirements.txt
└── README.md
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

> 使用 MinIO 需额外安装：`pip install minio`

### 2. （可选）启动 MinIO

```bash
docker run -d -p 9000:9000 -p 9001:9001 \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin \
  minio/minio server /data --console-address ":9001"
```

设置环境变量切换后端：

```bash
set STORAGE_BACKEND=minio
set MINIO_ENDPOINT=localhost:9000
set MINIO_ACCESS_KEY=minioadmin
set MINIO_SECRET_KEY=minioadmin
set MINIO_BUCKET=demo-files
```

### 3. 启动服务

```bash
cd "demo/06.文件上传下载系统"
uvicorn main:app --reload
```

预置用户：`alice`(id=1)、`bob`(id=2)。

## 接口一览

> 所有接口需 `X-User-Id` 请求头标识用户。

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/files/upload` | 上传文件（visibility 可选） |
| GET | `/files/` | 我的文件列表 |
| GET | `/files/public` | 公开文件列表（无需登录） |
| GET | `/files/{id}` | 文件元信息（需权限） |
| GET | `/files/{id}/download` | 下载文件（需权限） |
| PUT | `/files/{id}` | 修改可见性（仅 owner） |
| DELETE | `/files/{id}` | 删除文件（仅 owner） |
| POST | `/files/{id}/shares` | 共享给指定用户 |
| DELETE | `/files/{id}/shares/{uid}` | 取消共享 |

## 使用示例

### 1. 上传文件（alice）

```bash
curl -X POST http://127.0.0.1:8000/files/upload?visibility=private \
  -H "X-User-Id: 1" \
  -F "file=@photo.jpg"
```

### 2. 下载自己的文件

```bash
curl -OJ http://127.0.0.1:8000/files/1/download -H "X-User-Id: 1"
```

### 3. bob 尝试下载（private，应 403）

```bash
curl http://127.0.0.1:8000/files/1/download -H "X-User-Id: 2"
# {"detail":"无权下载该文件"}
```

### 4. alice 共享给 bob

```bash
curl -X POST http://127.0.0.1:8000/files/1/shares \
  -H "Content-Type: application/json" \
  -H "X-User-Id: 1" \
  -d '{"shared_with_user_id": 2}'
```

### 5. bob 再次下载（此时成功）

```bash
curl -OJ http://127.0.0.1:8000/files/1/download -H "X-User-Id: 2"
```

## 技术要点

- **存储后端抽象**：`StorageBackend` ABC，`LocalStorage` / `MinIOStorage` 实现统一接口，工厂方法按配置选择
- **存储 key 设计**：`{年}/{月}/{uuid}{ext}`，避免单目录文件过多
- **目录穿越防护**：`_path` 校验 resolve 后路径必须在 base_dir 之内
- **三级可见性**：public / private / shared，下载时统一走 `can_access_file` 判断
- **共享自动升级**：执行 `add_share` 时若非 shared 自动切换，避免遗漏
- **sha256 校验**：上传时计算 checksum，可用于去重 / 完整性校验
- **降级策略**：MinIO 连接失败自动降级本地存储，保证 Demo 可运行

## 扩展思路

- 接入 JWT 鉴权替换 `X-User-Id`
- 大文件分片上传（tus / multipart）
- 临时预签名 URL 下载（MinIO presigned URL）
- 文件去重（按 checksum 复用存储）
- 接入病毒扫描（ClamAV）
- 缩略图 / 图片处理（Pillow）
