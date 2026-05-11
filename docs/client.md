# client.py

CelestialTree 的 Python 客户端，支持 HTTP 和 gRPC 两种传输方式。

## Client

```python
Client(
    host: str = "127.0.0.1",
    http_port: int = 7777,
    grpc_port: int = 7778,
    timeout: float = 5.0,
    grpc_secure: bool = False,
    transport: Optional[str] = None,
)
```

### 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `host` | `str` | `"127.0.0.1"` | 服务地址 |
| `http_port` | `int` | `7777` | HTTP 端口 |
| `grpc_port` | `int` | `7778` | gRPC 端口 |
| `timeout` | `float` | `5.0` | 请求超时时间（秒） |
| `grpc_secure` | `bool` | `False` | 是否使用 TLS 连接 gRPC |
| `transport` | `Optional[str]` | `None` | 传输方式，`"http"` 或 `"grpc"`，默认 `"http"` |

---

## 方法

### init_session

```python
def init_session(self) -> None
```

初始化 HTTP 会话（懒加载，仅首次调用时创建）。会自动设置 `Content-Type` 和 `Accept` 为 `application/json`。

### init_grpc

```python
def init_grpc(self) -> None
```

初始化 gRPC channel 和 stub（懒加载，仅首次调用时创建）。根据 `grpc_secure` 选择安全或非安全通道。

### raise_for_status

```python
def raise_for_status(self, r: requests.Response) -> None
```

检查 HTTP 响应状态码，非 2xx 时抛出 `RuntimeError`。会尝试从响应 JSON 中提取 `error` 和 `detail` 字段。

---

### emit

```python
def emit(
    type_: str,
    parents: Optional[list[int]] = None,
    message: Optional[str] = None,
    payload: Optional[list[Any] | dict[str, Any]] = None,
) -> int
```

发射一个新事件到 CelestialTree，根据 `transport` 自动选择 HTTP 或 gRPC。

| 参数 | 类型 | 说明 |
|------|------|------|
| `type_` | `str` | 事件类型 |
| `parents` | `Optional[list[int]]` | 父事件 ID 列表 |
| `message` | `Optional[str]` | 事件消息 |
| `payload` | `Optional[list[Any] \| dict[str, Any]]` | 事件载荷 |

**返回值**: 新事件 ID（`int`）

### emit_http / emit_grpc

签名与 `emit` 相同，分别通过 HTTP 和 gRPC 发射事件。

> **gRPC 注意事项**: `payload` 通过 `google.protobuf.Struct` 传递。由于 Struct 不支持 list 作为根，list 类型的 payload 会被包装为 `{"_": payload}`。

---

### get_event

```python
def get_event(self, event_id: int) -> dict[str, Any]
```

获取指定事件的详细信息。

### children

```python
def children(self, event_id: int) -> list[int]
```

获取指定事件的直接子事件 ID 列表。

### ancestors

```python
def ancestors(self, event_id: int) -> list[int]
```

获取指定事件的所有祖先事件 ID 列表。

---

### descendants

```python
def descendants(self, event_id: int, view: str = "struct") -> dict[str, Any]
```

获取指定事件的后代树。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `event_id` | `int` | — | 事件 ID |
| `view` | `str` | `"struct"` | 视图格式，`"struct"` 或 `"meta"` |

### descendants_batch

```python
def descendants_batch(self, event_ids: list[int], view: str = "struct") -> list[dict[str, Any]]
```

批量获取多个事件的后代树。`event_ids` 不能为空，否则抛出 `ValueError`。

---

### provenance

```python
def provenance(self, event_id: int, view: str = "struct") -> dict[str, Any]
```

获取指定事件的溯源树（父链）。参数同 `descendants`。

### provenance_batch

```python
def provenance_batch(self, event_ids: list[int], view: str = "struct") -> list[dict[str, Any]]
```

批量获取多个事件的溯源树。参数同 `descendants_batch`。

---

### roots

```python
def roots(self) -> list[int]
```

获取所有根事件（无父节点）的 ID 列表。

### heads

```python
def heads(self) -> list[int]
```

获取所有叶子事件（无子节点）的 ID 列表。

### snapshot

```python
def snapshot(self) -> dict[str, Any]
```

获取当前事件图的快照。

### health

```python
def health(self) -> bool
```

检查服务健康状态。请求失败时返回 `False` 而非抛出异常。

### version

```python
def version(self) -> dict[str, Any]
```

获取服务版本信息。

---

### subscribe

```python
def subscribe(
    on_event: Callable[[dict[str, Any]], None],
    daemon: bool = True,
) -> threading.Thread
```

订阅 SSE 事件流。在后台线程中持续监听，每个事件触发 `on_event` 回调。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `on_event` | `Callable[[dict[str, Any]], None]` | — | 事件回调函数 |
| `daemon` | `bool` | `True` | 是否设置为守护线程 |

**返回值**: 监听线程（`threading.Thread`）
