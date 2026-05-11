from __future__ import annotations

import string, json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


class DotPathFormatter(string.Formatter):
    """
    支持点号和方括号路径的字符串格式化器。
    例如 "{payload.stage_tag}" 或 "{payload[stage_tag]}"。
    """

    def __init__(self, missing: str = ""):
        """
        初始化格式化器。

        :param missing: 字段缺失时的替代值
        """
        super().__init__()
        self.missing = missing

    def get_field(self, field_name: str, args: Any, kwargs: Any) -> tuple[Any, str]:
        # field_name 直接是完整的 "payload.stage_tag" 或 "payload[stage_tag]"
        return self._resolve_path(kwargs, field_name), field_name

    def _resolve_path(self, root: dict[str, Any], path: str) -> Any:
        """
        沿点号/方括号路径逐层解析值。

        :param root: 根字典
        :param path: 路径字符串，如 "payload.stage_tag"
        :return: 解析到的值，缺失时返回 self.missing
        """
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
        """
        将路径字符串拆分为 token 列表。

        :param path: 路径字符串
        :return: token 列表
        """
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
    """
    将 Unix 纳秒时间戳格式化为可读字符串。

    :param ts: Unix 纳秒时间戳
    :param tz: 时区，默认 UTC
    :return: 格式化后的时间字符串
    """
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
        """
        将节点渲染为标签字符串。

        :param node: 事件节点字典
        :return: 渲染后的标签
        """
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
    """
    递归格式化后代树中的单个节点及其子节点。

    :param node: 事件节点字典
    :param prefix: 当前行前缀
    :param is_last: 是否为同层最后一个节点
    :param label_style: 标签渲染风格
    :return: 格式化后的树字符串
    """
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
    """
    格式化一棵后代树（从根节点开始）。

    :param tree: 根节点字典
    :param label_style: 标签渲染风格
    :return: 格式化后的树字符串
    """
    lines: list[str] = [label_style.render(tree)]
    children: list[dict[str, Any]] = tree.get("children") or []
    for i, child in enumerate(children):
        lines.append(format_descendants(child, "", i == len(children) - 1, label_style))
    return "\n".join(lines)


def format_descendants_forest(
    forest: list[dict[str, Any]], label_style: NodeLabelStyle = DEFAULT_LABEL_STYLE
) -> str:
    """
    格式化多棵后代树（森林）。

    :param forest: 根节点列表
    :param label_style: 标签渲染风格
    :return: 格式化后的森林字符串
    """
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
    """
    递归格式化溯源树中的单个节点及其父节点。

    :param node: 事件节点字典
    :param prefix: 当前行前缀
    :param is_last: 是否为同层最后一个节点
    :param label_style: 标签渲染风格
    :return: 格式化后的树字符串
    """
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
    """
    格式化一棵溯源树（从根节点开始）。

    :param tree: 根节点字典
    :param label_style: 标签渲染风格
    :return: 格式化后的树字符串
    """
    lines: list[str] = [label_style.render(tree)]
    parents: list[dict[str, Any]] = tree.get("parents") or []
    for i, parent in enumerate(parents):
        lines.append(format_provenance(parent, "", i == len(parents) - 1, label_style))
    return "\n".join(lines)


def format_provenance_forest(
    forest: list[dict[str, Any]], label_style: NodeLabelStyle = DEFAULT_LABEL_STYLE
) -> str:
    """
    格式化多棵溯源树（森林）。

    :param forest: 根节点列表
    :param label_style: 标签渲染风格
    :return: 格式化后的森林字符串
    """
    lines: list[str] = []
    for tree in forest:
        lines.append(format_provenance_root(tree, label_style))
        lines.append("")
    return "\n".join(lines)
