from __future__ import annotations

import string, json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List


class DotPathFormatter(string.Formatter):
    def __init__(self, missing: str = ""):
        super().__init__()
        self.missing = missing

    def get_field(self, field_name, args, kwargs):
        # field_name 直接是完整的 "payload.stage_tag" 或 "payload[stage_tag]"
        return self._resolve_path(kwargs, field_name), field_name

    def _resolve_path(self, root: Dict[str, Any], path: str) -> Any:
        cur: Any = root

        # 支持 payload.stage_tag 形式
        # 也支持 payload[stage_tag] / payload['stage_tag']（format 里会把 [] 原样给到 key）
        tokens = self._tokenize(path)

        for t in tokens:
            if cur is None:
                return self.missing

            # dict key
            if isinstance(cur, dict):
                cur = cur.get(t, self.missing)
                continue

            # list/tuple index
            if isinstance(cur, (list, tuple)):
                try:
                    idx = int(t)
                    cur = cur[idx]
                except Exception:
                    return self.missing
                continue

            # attribute fallback（万一以后 node 不是 dict）
            if hasattr(cur, t):
                cur = getattr(cur, t)
                continue

            return self.missing

        return cur if cur is not None else self.missing

    def _tokenize(self, path: str):
        # 把 "payload.stage_tag" -> ["payload", "stage_tag"]
        # 把 "payload[stage_tag]" -> ["payload", "stage_tag"]
        # 把 "payload['stage_tag']" -> ["payload", "stage_tag"]
        tokens = []
        buf = ""
        i = 0
        while i < len(path):
            ch = path[i]
            if ch == ".":
                if buf:
                    tokens.append(buf)
                    buf = ""
                i += 1
                continue
            if ch == "[":
                if buf:
                    tokens.append(buf)
                    buf = ""
                j = path.find("]", i + 1)
                if j == -1:
                    # 不合法就当普通字符
                    buf += ch
                    i += 1
                    continue
                inner = path[i + 1 : j].strip().strip("'").strip('"')
                if inner:
                    tokens.append(inner)
                i = j + 1
                continue
            buf += ch
            i += 1
        if buf:
            tokens.append(buf)
        return tokens


def format_unix_nano(ts: int, tz=timezone.utc) -> str:
    sec = ts // 1_000_000_000
    ns = ts % 1_000_000_000
    dt = datetime.fromtimestamp(sec, tz=tz)
    return dt.strftime("%Y-%m-%d %H:%M:%S") + f".{ns // 1000:06d} UTC"


@dataclass(frozen=True)
class NodeLabelStyle:
    """
    模板渲染风格：
    - template: 例如 "{base} ({type}) @{time}"
    - missing: 字段缺失时的替代值（默认 `-` ）
    """
    template: str = "{base} ({type}) @{time}"
    missing: str = "-"

    def render(self, node: Dict[str, Any]) -> str:
        ctx: Dict[str, Any] = dict(node)

        # -------- 派生字段 --------
        node_id, is_ref = node.get("id"), node.get("is_ref")
        ctx.setdefault("base", f"{node_id} [Ref]" if is_ref else node_id)

        ts = node.get("time_unix_nano")
        ctx.setdefault(
            "time",
            format_unix_nano(ts) if ts is not None else self.missing
        )

        ctx.setdefault("payload_json", json.dumps(node.get("payload"), ensure_ascii=False, sort_keys=True))

        formatter = DotPathFormatter(missing=self.missing)
        return formatter.format(self.template, **ctx)

DEFAULT_LABEL_STYLE = NodeLabelStyle()

# ------------------- 你的树格式化：加一个 label_style 参数 -------------------

def format_descendants(
    node: Dict[str, Any],
    prefix: str = "",
    is_last: bool = True,
    label_style: NodeLabelStyle = DEFAULT_LABEL_STYLE,
) -> str:
    lines = []
    connector = "╘-->" if is_last else "╞-->"
    lines.append(f"{prefix}{connector}{label_style.render(node)}")

    children = node.get("children") or []
    if children:
        next_prefix = prefix + ("    " if is_last else "│   ")
        for i, child in enumerate(children):
            lines.append(
                format_descendants(child, next_prefix, i == len(children) - 1, label_style)
            )

    return "\n".join(lines)


def format_descendants_root(tree: Dict[str, Any], label_style: NodeLabelStyle = DEFAULT_LABEL_STYLE) -> str:
    lines = [label_style.render(tree)]
    children = tree.get("children") or []
    for i, child in enumerate(children):
        lines.append(format_descendants(child, "", i == len(children) - 1, label_style))
    return "\n".join(lines)


def format_descendants_forest(forest: List[Dict[str, Any]], label_style: NodeLabelStyle = DEFAULT_LABEL_STYLE) -> str:
    lines = []
    for tree in forest:
        lines.append(format_descendants_root(tree, label_style))
        lines.append("")
    return "\n".join(lines)


def format_provenance(
    node: Dict[str, Any],
    prefix: str = "",
    is_last: bool = True,
    label_style: NodeLabelStyle = DEFAULT_LABEL_STYLE,
) -> str:
    lines = []
    connector = "╘<--" if is_last else "╞<--"
    lines.append(f"{prefix}{connector}{label_style.render(node)}")

    parents = node.get("parents") or []
    if parents:
        next_prefix = prefix + ("    " if is_last else "│   ")
        for i, parent in enumerate(parents):
            lines.append(format_provenance(parent, next_prefix, i == len(parents) - 1, label_style))

    return "\n".join(lines)


def format_provenance_root(tree: Dict[str, Any], label_style: NodeLabelStyle = DEFAULT_LABEL_STYLE) -> str:
    lines = [label_style.render(tree)]
    parents = tree.get("parents") or []
    for i, parent in enumerate(parents):
        lines.append(format_provenance(parent, "", i == len(parents) - 1, label_style))
    return "\n".join(lines)


def format_provenance_forest(forest: List[Dict[str, Any]], label_style: NodeLabelStyle = DEFAULT_LABEL_STYLE) -> str:
    lines = []
    for tree in forest:
        lines.append(format_provenance_root(tree, label_style))
        lines.append("")
    return "\n".join(lines)
