# tools/formatters.py

事件树的文本格式化工具，用于将后代树和溯源树渲染为可读的 ASCII 树形字符串。

## DotPathFormatter

```python
DotPathFormatter(missing: str = "")
```

继承自 `string.Formatter`，支持点号和方括号路径的字符串格式化器。

### 路径语法

- 点号访问: `{payload.stage_tag}`
- 方括号访问: `{payload[stage_tag]}`
- 引号方括号: `{payload['stage_tag']}`
- 嵌套路径: `{payload.nested.field}`
- 列表索引: `{items[0]}`

### 方法

#### _resolve_path

```python
def _resolve_path(self, root: dict[str, Any], path: str) -> Any
```

沿点号/方括号路径逐层解析值。支持 dict 键访问、list/tuple 索引、属性回退三种方式。

#### _tokenize

```python
def _tokenize(self, path: str) -> list[str]
```

将路径字符串拆分为 token 列表。

示例:
- `"payload.stage_tag"` → `["payload", "stage_tag"]`
- `"payload[stage_tag]"` → `["payload", "stage_tag"]`
- `"payload['stage_tag']"` → `["payload", "stage_tag"]`

---

## format_unix_nano

```python
def format_unix_nano(ts: int, tz=timezone.utc) -> str
```

将 Unix 纳秒时间戳格式化为可读字符串。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `ts` | `int` | — | Unix 纳秒时间戳 |
| `tz` | `timezone` | `timezone.utc` | 时区 |

**输出格式**: `"2024-01-15 08:30:00.123456 UTC"`

---

## NodeLabelStyle

```python
@dataclass(frozen=True)
class NodeLabelStyle:
    template: str = "{base} ({type}) @{time}"
    missing: str = "-"
```

模板渲染风格配置（不可变 dataclass）。

### 字段

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `template` | `str` | `"{base} ({type}) @{time}"` | 渲染模板 |
| `missing` | `str` | `"-"` | 字段缺失时的替代值 |

### 内置派生字段

在 `render` 时自动生成以下字段（如果节点中不存在）：

| 字段 | 说明 |
|------|------|
| `base` | 节点 ID，若 `is_ref` 为真则追加 `[Ref]` |
| `time` | 从 `time_unix_nano` 格式化的可读时间 |
| `payload_json` | payload 的 JSON 字符串 |

### render

```python
def render(self, node: dict[str, Any]) -> str
```

将节点渲染为标签字符串。模板中可使用节点的任意字段以及上述派生字段，支持 `DotPathFormatter` 的路径语法。

---

## 后代树格式化

### format_descendants

```python
def format_descendants(
    node: dict[str, Any],
    prefix: str = "",
    is_last: bool = True,
    label_style: NodeLabelStyle = DEFAULT_LABEL_STYLE,
) -> str
```

递归格式化后代树中的单个节点及其子节点。使用 `╘-->` / `╞-->` 作为连接符。

### format_descendants_root

```python
def format_descendants_root(tree: dict[str, Any], label_style=DEFAULT_LABEL_STYLE) -> str
```

格式化一棵完整的后代树（从根节点开始，根节点无连接符前缀）。

### format_descendants_forest

```python
def format_descendants_forest(forest: list[dict[str, Any]], label_style=DEFAULT_LABEL_STYLE) -> str
```

格式化多棵后代树（森林），各树之间以空行分隔。

---

## 溯源树格式化

### format_provenance

```python
def format_provenance(
    node: dict[str, Any],
    prefix: str = "",
    is_last: bool = True,
    label_style: NodeLabelStyle = DEFAULT_LABEL_STYLE,
) -> str
```

递归格式化溯源树中的单个节点及其父节点。使用 `╘<--` / `╞<--` 作为连接符。

### format_provenance_root

```python
def format_provenance_root(tree: dict[str, Any], label_style=DEFAULT_LABEL_STYLE) -> str
```

格式化一棵完整的溯源树（从根节点开始）。

### format_provenance_forest

```python
def format_provenance_forest(forest: list[dict[str, Any]], label_style=DEFAULT_LABEL_STYLE) -> str
```

格式化多棵溯源树（森林），各树之间以空行分隔。

---

## 输出示例

```
3 (process) @2024-01-15 08:30:00.000000 UTC
╞-->4 (step) @2024-01-15 08:30:01.000000 UTC
│   ╘-->6 (result) @2024-01-15 08:30:02.000000 UTC
╘-->5 (step) @2024-01-15 08:30:01.500000 UTC
```
