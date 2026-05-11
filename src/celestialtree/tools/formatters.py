from __future__ import annotations

import string, json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


class DotPathFormatter(string.Formatter):
    def __init__(self, missing: str = ""):
        super().__init__()
        self.missing = missing

    def get_field(self, field_name: str, args: Any, kwargs: Any) -> tuple[Any, str]:
        # field_name 直接是完整的 "payload.stage_tag" 或 "payload[stage_tag]"
        return self._resolve_path(kwargs, field_name), field_name

    def _resolve_path(self, root: dict[str, Any], path: str) -> Any:
        cur: Any = root

        # 支持 payload.stage_tag 形式
        # 也支持 payload[stage_tag] / payload['stage_tag']
        tokens = self._tokenize(path)

        for t in tokens:
            if cur is None:
                return self.missing

            if isinstance(cur, dict):
                cur = cur.get(t, self.missing) # type: ignore[reportUnknownVariableType]
            elif isinstance(cur, (list, tuple)):
                try:
                    cur = cur[int(t)] # type: ignore[reportUnknownVariableType]
                except Exception:
                    return self.missing
            elif hasattr(cur, t):  # type: ignore[reportUnknownArgumentType]  # attribute fallback
                cur = getattr(cur, str(t))  # type: ignore[reportUnknownArgumentType]
            else:
                return self.missing

        return cur  # type: ignore[reportUnknownVariableType]

    def _tokenize(self, path: str) -> list[str]:
        # "payload.stage_tag" -> ["payload", "stage_tag"]
        # "payload[stage_tag]" -> ["payload", "stage_tag"]
        # "payload['stage_tag']" -> ["payload", "stage_tag"]
        tokens: list[str] = []
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


def format_unix_nano(ts: int, tz: Any = timezone.utc) -> str:
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

    def render(self, node: dict[str, Any]) -> str:
        ctx: dict[str, Any] = dict(node)

        node_id, is_ref = node.get("id"), node.get("is_ref")
        ctx.setdefault("base", f"{node_id} [Ref]" if is_ref else node_id)

        ts = node.get("time_unix_nano")
        ctx.setdefault("time", format_unix_nano(ts) if ts is not None else self.missing)

        ctx.setdefault(
            "payload_json",
            json.dumps(node.get("payload"), ensure_ascii=False, sort_keys=True),
        )

        formatter = DotPathFormatter(missing=self.missing)
        return formatter.format(self.template, **ctx)


DEFAULT_LABEL_STYLE = NodeLabelStyle()


def format_descendants(
    node: dict[str, Any],
    prefix: str = "",
    is_last: bool = True,
    label_style: NodeLabelStyle = DEFAULT_LABEL_STYLE,
) -> str:
    lines: list[str] = []
    connector = "╘-->" if is_last else "╞-->"
    lines.append(f"{prefix}{connector}{label_style.render(node)}")

    children: list[dict[str, Any]] = node.get("children") or []
    if children:
        next_prefix = prefix + ("    " if is_last else "│   ")
        for i, child in enumerate(children):
            lines.append(
                format_descendants(
                    child, next_prefix, i == len(children) - 1, label_style
                )
            )

    return "\n".join(lines)


def format_descendants_root(
    tree: dict[str, Any], label_style: NodeLabelStyle = DEFAULT_LABEL_STYLE
) -> str:
    lines: list[str] = [label_style.render(tree)]
    children: list[dict[str, Any]] = tree.get("children") or []
    for i, child in enumerate(children):
        lines.append(format_descendants(child, "", i == len(children) - 1, label_style))
    return "\n".join(lines)


def format_descendants_forest(
    forest: list[dict[str, Any]], label_style: NodeLabelStyle = DEFAULT_LABEL_STYLE
) -> str:
    lines: list[str] = []
    for tree in forest:
        lines.append(format_descendants_root(tree, label_style))
        lines.append("")
    return "\n".join(lines)


def format_provenance(
    node: dict[str, Any],
    prefix: str = "",
    is_last: bool = True,
    label_style: NodeLabelStyle = DEFAULT_LABEL_STYLE,
) -> str:
    lines: list[str] = []
    connector = "╘<--" if is_last else "╞<--"
    lines.append(f"{prefix}{connector}{label_style.render(node)}")

    parents: list[dict[str, Any]] = node.get("parents") or []
    if parents:
        next_prefix = prefix + ("    " if is_last else "│   ")
        for i, parent in enumerate(parents):
            lines.append(
                format_provenance(
                    parent, next_prefix, i == len(parents) - 1, label_style
                )
            )

    return "\n".join(lines)


def format_provenance_root(
    tree: dict[str, Any], label_style: NodeLabelStyle = DEFAULT_LABEL_STYLE
) -> str:
    lines: list[str] = [label_style.render(tree)]
    parents: list[dict[str, Any]] = tree.get("parents") or []
    for i, parent in enumerate(parents):
        lines.append(format_provenance(parent, "", i == len(parents) - 1, label_style))
    return "\n".join(lines)


def format_provenance_forest(
    forest: list[dict[str, Any]], label_style: NodeLabelStyle = DEFAULT_LABEL_STYLE
) -> str:
    lines: list[str] = []
    for tree in forest:
        lines.append(format_provenance_root(tree, label_style))
        lines.append("")
    return "\n".join(lines)
