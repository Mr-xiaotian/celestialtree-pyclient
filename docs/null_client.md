# null_client.py

空实现的 CelestialTree 客户端，用于测试或不需要实际连接的场景。

## NullClient

```python
NullClient(event_id: Optional[int] = None)
```

### 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `event_id` | `Optional[int]` | `None` | 初始事件 ID，默认从 0 开始 |

### 行为

- `emit` / `emit_grpc`: 使用本地自增 ID，每次调用返回递增的事件 ID
- `get_event`: 返回 `None`
- `children` / `ancestors` / `roots` / `heads`: 返回空列表 `[]`
- `descendants` / `descendants_batch` / `provenance` / `provenance_batch`: 返回 `None`
- `snapshot` / `version`: 返回空字典 `{}`
- `health`: 返回 `True`
- `subscribe`: 返回 `None`

### 使用场景

```python
from celestialtree import NullClient

# 在测试中替代真实客户端
client = NullClient()
eid = client.emit("test")  # 返回 1
eid = client.emit("test")  # 返回 2
```

> **注意**: `NullClient` 不是进程安全的。如果需要在多进程环境下使用，需自行传入共享的 `event_id`。
