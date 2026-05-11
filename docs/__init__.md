# celestialtree

包的顶层入口模块。

## 导出内容

| 名称 | 来源 | 说明 |
|------|------|------|
| `Client` | `client.py` | CelestialTree HTTP/gRPC 客户端 |
| `NullClient` | `null_client.py` | 空实现客户端，用于测试 |
| `NodeLabelStyle` | `tools/formatters.py` | 节点标签渲染风格配置 |
| `format_descendants_root` | `tools/formatters.py` | 格式化单棵后代树 |
| `format_provenance_root` | `tools/formatters.py` | 格式化单棵溯源树 |
| `format_descendants_forest` | `tools/formatters.py` | 格式化多棵后代树（森林） |
| `format_provenance_forest` | `tools/formatters.py` | 格式化多棵溯源树（森林） |

## 快速开始

```python
from celestialtree import Client

client = Client(host="127.0.0.1", http_port=7777)
event_id = client.emit("start", message="hello")
print(client.get_event(event_id))
```
