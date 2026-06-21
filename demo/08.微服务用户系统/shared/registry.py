"""服务注册中心（进程内，运行于 api-gateway）。

思想：
- 各微服务启动时向网关注册自身（name + host + port）
- 服务定期发送心跳，超时未心跳视为下线（健康检查）
- 网关从注册表中选择健康实例转发请求（服务发现 + 负载均衡）

Demo 用进程内字典实现；生产环境应使用 Consul / etcd / Nacos。
"""

import threading
import time
from dataclasses import dataclass, field


@dataclass
class ServiceInstance:
    name: str
    host: str
    port: int
    last_heartbeat: float = field(default_factory=time.time)

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def is_healthy(self, ttl: float = 15.0) -> bool:
        return (time.time() - self.last_heartbeat) < ttl


class ServiceRegistry:
    def __init__(self, heartbeat_ttl: float = 15.0) -> None:
        self.heartbeat_ttl = heartbeat_ttl
        self._instances: dict[str, list[ServiceInstance]] = {}
        self._lock = threading.Lock()
        # 简单轮询计数器
        self._rr: dict[str, int] = {}

    def register(self, name: str, host: str, port: int) -> ServiceInstance:
        with self._lock:
            instances = self._instances.setdefault(name, [])
            # 同地址更新而非新增
            for ins in instances:
                if ins.host == host and ins.port == port:
                    ins.last_heartbeat = time.time()
                    return ins
            ins = ServiceInstance(name=name, host=host, port=port)
            instances.append(ins)
            return ins

    def heartbeat(self, name: str, host: str, port: int) -> bool:
        with self._lock:
            for ins in self._instances.get(name, []):
                if ins.host == host and ins.port == port:
                    ins.last_heartbeat = time.time()
                    return True
            return False

    def deregister(self, name: str, host: str, port: int) -> None:
        with self._lock:
            instances = self._instances.get(name, [])
            self._instances[name] = [
                i for i in instances if not (i.host == host and i.port == port)
            ]

    def healthy_instances(self, name: str) -> list[ServiceInstance]:
        with self._lock:
            return [
                i
                for i in self._instances.get(name, [])
                if i.is_healthy(self.heartbeat_ttl)
            ]

    def discover(self, name: str) -> ServiceInstance | None:
        """服务发现：轮询选择一个健康实例。"""
        healthy = self.healthy_instances(name)
        if not healthy:
            return None
        with self._lock:
            idx = self._rr.get(name, 0) % len(healthy)
            self._rr[name] = idx + 1
        return healthy[idx]

    def all_services(self) -> dict[str, list[dict]]:
        result: dict[str, list[dict]] = {}
        for name, instances in self._instances.items():
            result[name] = [
                {
                    "host": i.host,
                    "port": i.port,
                    "base_url": i.base_url,
                    "healthy": i.is_healthy(self.heartbeat_ttl),
                    "last_heartbeat": i.last_heartbeat,
                }
                for i in instances
            ]
        return result


# 网关进程内的全局注册表
registry = ServiceRegistry()
