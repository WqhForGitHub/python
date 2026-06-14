# 58. REST API（仅 Python 实现）

仅依赖 Python 标准库的 RESTful API 服务，演示 CRUD。

## 资源
| Method | URL | 说明 |
|--------|-----|------|
| GET | /users | 列出全部 |
| GET | /users/{id} | 获取单个 |
| POST | /users | 创建（JSON: {"name":"..","age":..}）|
| PUT | /users/{id} | 更新 |
| DELETE | /users/{id} | 删除 |

数据持久化为 `data.json`。

## 运行
```
python rest_api.py
```

## 测试
```
curl http://127.0.0.1:5000/users
curl -X POST -H "Content-Type: application/json" -d "{\"name\":\"Tom\",\"age\":20}" http://127.0.0.1:5000/users
curl http://127.0.0.1:5000/users/1
curl -X PUT -H "Content-Type: application/json" -d "{\"age\":21}" http://127.0.0.1:5000/users/1
curl -X DELETE http://127.0.0.1:5000/users/1
```
