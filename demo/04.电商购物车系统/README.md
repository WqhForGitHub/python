# 04. 电商购物车系统 (FastAPI Demo)

基于 FastAPI 的电商购物车系统 Demo，包含 **商品查询（Redis 缓存）**、**购物车（Redis 存储）**、**下单接口（扣库存 / 订单明细快照）**。

## 功能特性

| 模块 | 说明 |
| --- | --- |
| 商品查询 | 商品列表分页、关键词搜索、详情带 Redis 缓存 |
| 购物车 | 基于 Redis Hash 存储，支持增 / 删 / 改 / 查，自动校验库存 |
| 下单接口 | 从购物车一键下单，扣减库存，生成订单与明细快照 |
| 订单管理 | 订单列表 / 详情 / 支付 / 取消（取消归还库存） |
| 缓存降级 | 无 Redis 环境自动降级为进程内内存缓存，Demo 可直接运行 |

## 项目结构

```
04.电商购物车系统/
├── main.py                # 应用入口 + 示例数据
├── config.py              # 配置（数据库 / Redis / TTL）
├── database.py            # 引擎 / Session
├── models.py              # ORM 模型 (Product / Order / OrderItem)
├── schemas.py             # Pydantic 模型
├── cache.py               # Redis 客户端 + 内存降级 + 购物车操作
├── crud/
│   ├── __init__.py
│   ├── product.py         # 商品 CRUD + 缓存
│   ├── cart.py            # 购物车业务（Redis）
│   └── order.py           # 订单业务（下单 / 支付 / 取消）
├── routers/
│   ├── __init__.py
│   ├── products.py        # 商品路由
│   ├── cart.py            # 购物车路由（X-User-Id）
│   └── orders.py          # 订单路由
├── requirements.txt
└── README.md
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. （可选）启动 Redis

```bash
docker run -d -p 6379:6379 redis:7
```

> 若未启动 Redis，Demo 会自动降级为内存缓存，功能一致但不具备分布式能力。

### 3. 启动服务

```bash
cd "demo/04.电商购物车系统"
uvicorn main:app --reload
```

首次启动会自动建表并写入 3 个示例商品。

### 4. 访问

| 地址 | 说明 |
| --- | --- |
| http://127.0.0.1:8000/ | 欢迎页（显示当前缓存模式） |
| http://127.0.0.1:8000/docs | Swagger UI |

## 接口一览

### 商品 `/products`

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/products/` | 创建商品 |
| GET | `/products/` | 商品列表（分页 / 关键词） |
| GET | `/products/{id}` | 商品详情（带缓存） |
| PUT | `/products/{id}` | 更新商品 |
| DELETE | `/products/{id}` | 删除商品 |

### 购物车 `/cart`（需 `X-User-Id` 头）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/cart/` | 查看购物车 |
| POST | `/cart/items` | 加入购物车 |
| PUT | `/cart/items/{pid}` | 修改数量 |
| DELETE | `/cart/items/{pid}` | 移除商品 |
| DELETE | `/cart/` | 清空购物车 |

### 订单 `/orders`

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/orders/` | 从购物车下单 |
| GET | `/orders/` | 订单列表（可按 user_id 筛选） |
| GET | `/orders/{id}` | 订单详情 |
| POST | `/orders/{id}/pay` | 支付订单 |
| POST | `/orders/{id}/cancel` | 取消订单（归还库存） |

## 使用示例

### 1. 加入购物车

```bash
curl -X POST http://127.0.0.1:8000/cart/items \
  -H "Content-Type: application/json" \
  -H "X-User-Id: 1" \
  -d '{"product_id": 1, "quantity": 2}'
```

### 2. 查看购物车

```bash
curl http://127.0.0.1:8000/cart/ -H "X-User-Id: 1"
```

### 3. 下单

```bash
curl -X POST http://127.0.0.1:8000/orders/ \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "address": "北京市海淀区"}'
```

## 技术要点

- **Redis Hash 购物车**：`cart:{user_id}` 存储商品数量，O(1) 读写
- **缓存降级**：连接 Redis 失败时自动切换内存字典，保证 Demo 可运行
- **库存扣减**：下单时二次校验库存，扣减失败回滚
- **订单明细快照**：`OrderItem` 保存下单时的商品名 / 价格，避免后续商品修改影响历史订单
- **取消归还库存**：取消订单时将数量加回商品库存
- **缓存失效**：商品更新 / 删除时清除对应缓存 key

## 扩展思路

- 引入 JWT 鉴权替换 `X-User-Id`
- 库存扣减使用乐观锁（version 字段）
- 接入支付沙箱（如支付宝 / 微信）
- 商品列表也缓存（key 带分页 + 关键词）
- 引入消息队列异步处理订单
