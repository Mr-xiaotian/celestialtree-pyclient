# proto/celestialtree_pb2_grpc.py

由 `grpc_tools` 自动生成的 gRPC 服务桩模块。**请勿手动编辑。**

## 服务定义

### CelestialTreeService

| 方法 | 请求类型 | 响应类型 | 模式 | 说明 |
|------|----------|----------|------|------|
| `Emit` | `EmitRequest` | `EmitResponse` | Unary-Unary | 发射一个新事件 |

## 导出的类

### CelestialTreeServiceStub

gRPC 客户端桩，用于调用远程 `CelestialTreeService`。

```python
stub = CelestialTreeServiceStub(channel)
response = stub.Emit(request, timeout=5.0)
```

### CelestialTreeServiceServicer

gRPC 服务端基类，需继承并实现 `Emit` 方法。

### add_CelestialTreeServiceServicer_to_server

```python
def add_CelestialTreeServiceServicer_to_server(servicer, server)
```

将 servicer 实例注册到 gRPC server。
