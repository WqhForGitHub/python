# REST API（仅 Python 标准库）

> 注：根据用户指示，本 demo 放置在「72. CLI 包管理工具」目录下。

仅使用 socket/json/threading 实现的 RESTful API 框架，演示用户资源 CRUD。

## 端点
| 方法 | 路径 | 说明 |
|---|---|---|
| GET    | `/api/users`         | 列表，支持 `?q=&limit=&offset=` |
| GET    | `/api/users/<id>`    | 详情 |
| POST   | `/api/users`         | 创建 |
| PUT    | `/api/users/<id>`    | 全量更新 |
| PATCH  | `/api/users/<id>`    | 部分更新 |
| DELETE | `/api/users/<id>`    | 删除 |

## 用法
```bash
python rest_api.py
curl http://localhost:8001/api/users
curl -X POST -H "Content-Type: application/json" \
  -d '{"name":"Carol","email":"c@x.com","age":28}' \
  http://localhost:8001/api/users
```
