# proto/celestialtree_pb2.py

由 `protoc` 自动生成的 protobuf 消息定义模块。**请勿手动编辑。**

## 源 proto 文件

`celestialtree/proto/celestialtree.proto`

## 消息类型

### EmitRequest

发射事件的请求消息。

| 字段 | 类型 | 编号 | 说明 |
|------|------|------|------|
| `type` | `string` | 1 | 事件类型 |
| `message` | `string` | 2 | 事件消息 |
| `payload` | `google.protobuf.Struct` | 3 | 事件载荷（JSON 对象） |
| `parents` | `repeated uint64` | 4 | 父事件 ID 列表 |

### EmitResponse

发射事件的响应消息。

| 字段 | 类型 | 编号 | 说明 |
|------|------|------|------|
| `id` | `uint64` | 1 | 新创建的事件 ID |

## 重新生成

```bash
python -m grpc_tools.protoc \
    -I. \
    --python_out=. \
    --grpc_python_out=. \
    celestialtree/proto/celestialtree.proto
```
