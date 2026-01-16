# CelestialTree PyClient

A lightweight Python client for interacting with **CelestialTree**, providing event emission, lineage tracking, and basic querying capabilities.

This client is designed to be embedded into task systems (such as CelestialFlow) to record and trace the lifecycle of tasks through a causal event tree.

## Features

- Emit structured events to a CelestialTree service
- Track parent–child relationships between events
- Designed for task execution and orchestration systems
- Simple, dependency-light Python interface

## Installation

```bash
pip install celestialtree
```

## Usage

```python
from celestialtree import Client

client = Client(
    base_url="http://localhost:7777",
)

event_id = client.emit(
    event_type="task.success",
    parents=[123456],
    message="Task completed successfully"
)

print(event_id)
```

## Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.