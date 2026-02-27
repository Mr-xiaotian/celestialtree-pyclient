# CelestialTree PyClient

一个轻量级的 Python 客户端，用于与 [CelestialTree](https://github.com/Mr-xiaotian/CelestialTree) 交互，提供事件上报、血缘（lineage）追踪以及基础查询能力。

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

## Star 历史趋势（Star History）

如果对项目感兴趣的话，欢迎star。如果有问题或者建议的话, 欢迎提交[Issues](https://github.com/Mr-xiaotian/celestialtree-pyclient/issues)或者在[Discussion](https://github.com/Mr-xiaotian/celestialtree-pyclient/discussions)中告诉我。

[![Star History Chart](https://api.star-history.com/svg?repos=Mr-xiaotian/celestialtree-pyclient&type=Date)](https://star-history.com/#Mr-xiaotian/celestialtree-pyclient&Date)

## 许可（License）
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 作者（Author）
Author: Mr-xiaotian
Email: mingxiaomingtian@gmail.com
Project Link: [https://github.com/Mr-xiaotian/celestialtree-pyclient](https://github.com/Mr-xiaotian/celestialtree-pyclient)

