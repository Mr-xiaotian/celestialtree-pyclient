# CelestialTree PyClient

一个轻量级的 Python 客户端，用于与 **CelestialTree** 交互，提供事件上报、血缘（lineage）追踪以及基础查询能力。

该客户端被设计为可嵌入到任务系统中（例如 CelestialFlow），用于记录并追踪任务在因果事件树中的完整生命周期。

## 功能特性

* 向 CelestialTree 服务发送结构化事件
* 追踪事件之间的父子关系
* 面向任务执行与编排系统进行设计
* 接口简洁、依赖极少的 Python 客户端

## 安装

```bash
pip install celestialtree
```

## 使用示例

```python
from celestialtree import Client

client = Client(
    base_url="http://localhost:7777",
)

event_id = client.emit(
    event_type="task.success",
    parents=[123456],
    message="任务成功完成"
)

print(event_id)
```

## 参与贡献

欢迎任何形式的贡献！你可以提交 issue、功能请求，或者直接发起 pull request。

## 许可证

本项目采用 MIT License 许可证，详情请参阅 [LICENSE](LICENSE) 文件。
