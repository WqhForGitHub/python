# 05. 即时聊天系统 (FastAPI Demo)

基于 FastAPI **WebSocket** 的即时聊天系统 Demo，支持 **在线状态**、**群聊**、**私聊**、**消息历史**。

## 功能特性

| 模块 | 说明 |
| --- | --- |
| WebSocket 实时通信 | `ws://host/ws/chat?user_id=N` 长连接双向通信 |
| 在线状态 | 用户上下线自动广播，`/rooms/online` 查询在线列表 |
| 群聊 | 加入房间后消息广播给房间内所有在线成员 |
| 私聊 | 点对点投递，离线时返回 `delivered:false` |
| 消息历史 | 进程内定长队列保存最近消息，HTTP 接口查询 |
| 单点登录 | 同一用户重复登录自动踢掉旧连接 |
| 心跳保活 | 客户端定时发送 heartbeat，服务端回 pong |
| 内置聊天页 | `/static/index.html` 可视化聊天客户端 |

## 项目结构

```
05.即时聊天系统/
├── main.py                # 应用入口 + 静态文件挂载
├── config.py              # 心跳间隔 / 历史保留条数
├── manager.py             # 连接管理器（在线状态 / 房间 / 消息分发）
├── store.py               # 消息历史存储（进程内定长队列）
├── schemas.py             # WS 消息信封模型
├── routers/
│   ├── __init__.py
│   ├── rooms.py           # 房间 / 在线状态 / 历史 HTTP 接口
│   └── chat.py            # WebSocket 端点
├── static/
│   └── index.html         # 可视化聊天客户端
├── requirements.txt
└── README.md
```

## 快速开始

```bash
pip install -r requirements.txt
cd "demo/05.即时聊天系统"
uvicorn main:app --reload
```

### 体验对话

1. 用两个浏览器标签页打开 `http://127.0.0.1:8000/static/index.html`
2. 第一个标签 user_id 填 `1`，点击「连接」
3. 第二个标签 user_id 填 `2`，点击「连接」
4. 群聊：两边房间都填 `general`，点击「加入房间」，然后发送消息
5. 私聊：一边「私聊给」填对方 ID，直接发送

## 消息协议

### 客户端 -> 服务端

```jsonc
// 群聊
{"type": "chat", "room": "general", "content": "hello"}
// 私聊
{"type": "chat", "to": 2, "content": "hi"}
// 加入房间
{"type": "join", "room": "general"}
// 离开房间
{"type": "leave", "room": "general"}
// 心跳
{"type": "heartbeat"}
```

### 服务端 -> 客户端

```jsonc
{
  "type": "chat",          // chat | join | leave | system | heartbeat
  "room": "general",
  "from": 1,               // 0 表示系统
  "to": null,              // 私聊时为接收者
  "content": "hello",
  "timestamp": "2026-06-20T10:00:00.123456Z"
}
```

## HTTP 接口一览

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/rooms/online` | 在线用户列表 |
| GET | `/rooms/` | 所有房间 |
| GET | `/rooms/{room}/members` | 房间在线成员 |
| GET | `/rooms/{room}/history` | 房间消息历史 |
| GET | `/rooms/dm/{u1}/{u2}/history` | 私聊会话历史 |

## 技术要点

- **ConnectionManager 单例**：集中管理 `user_id -> WebSocket` 与 `room -> set(user_id)` 两个映射
- **私聊房间命名**：`dm:{min(uid1,uid2)}_{max(uid1,uid2)}` 保证两人会话唯一
- **单点登录**：重复登录主动关闭旧连接（code 4001），避免消息重复投递
- **离线投递标记**：私聊接收方离线时 `delivered:false`，仅记录历史不丢失
- **消息历史**：`deque(maxlen=N)` 自动淘汰旧消息
- **心跳保活**：客户端 25s 发一次 heartbeat，服务端回 pong

## 扩展思路

- 消息历史落库（PostgreSQL）+ 分页查询
- 接入 Redis Pub/Sub 支持多实例水平扩展
- 用户鉴权（WebSocket 子协议 / 首帧 token）
- 消息已读回执 / 撤回
- 离线消息推送（接入 APNs / FCM）
- 文件 / 图片消息
