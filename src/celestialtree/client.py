import json
import threading
import requests
from typing import Optional, Any, Callable

import grpc
from google.protobuf import json_format
from google.protobuf.struct_pb2 import Struct

from .proto import celestialtree_pb2 as pb2
from .proto import celestialtree_pb2_grpc as pb2_grpc


class Client:
    """
    Python client for CelestialTree HTTP API (and optional gRPC).
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        http_port: int = 7777,
        grpc_port: int = 7778,
        timeout: float = 5.0,
        grpc_secure: bool = False,
        transport: Optional[str] = None,
    ):
        """
        初始化 CelestialTree 客户端。

        :param host: 服务地址
        :param http_port: HTTP 端口
        :param grpc_port: gRPC 端口
        :param timeout: 请求超时时间（秒）
        :param grpc_secure: 是否使用 TLS 连接 gRPC
        :param transport: 传输方式，"http" 或 "grpc"，默认 "http"
        """
        self.http_addr = f"http://{host}:{http_port}"
        self.grpc_addr = f"{host}:{grpc_port}"

        self.timeout = timeout
        self.grpc_secure = grpc_secure

        self.transport = transport if transport in ("http", "grpc") else "http"

    def init_session(self):
        """
        初始化 HTTP 会话（懒加载，仅首次调用时创建）。
        """
        if hasattr(self, "session"):
            return

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

    def init_grpc(self):
        """
        初始化 gRPC channel 和 stub（懒加载，仅首次调用时创建）。
        """
        if hasattr(self, "grpc_channel") and hasattr(self, "grpc_stub"):
            return

        if self.grpc_secure:
            creds = grpc.ssl_channel_credentials()
            self.grpc_channel = grpc.secure_channel(self.grpc_addr, creds)
        else:
            self.grpc_channel = grpc.insecure_channel(self.grpc_addr)

        self.grpc_stub = pb2_grpc.CelestialTreeServiceStub(self.grpc_channel)

    def raise_for_status(self, r: requests.Response) -> None:
        """
        检查 HTTP 响应状态码，非 2xx 时抛出 RuntimeError。

        :param r: HTTP 响应对象
        """
        if 200 <= r.status_code < 300:
            return

        try:
            j: dict[str, Any] = r.json()
            error = j.get("error", "request failed")
            detail = j.get("detail")
            raise RuntimeError(f"{error} ({detail})" if detail else str(error))
        except Exception:
            raise RuntimeError(f"request failed: HTTP {r.status_code}: {r.text[:300]}")

    # ---------- Core APIs ----------

    def emit(
        self,
        type_: str,
        parents: Optional[list[int]] = None,
        message: Optional[str] = None,
        payload: Optional[list[Any] | dict[str, Any]] = None,
    ) -> int:
        """
        发射一个新事件到 CelestialTree，根据 transport 选择 HTTP 或 gRPC。

        :param type_: 事件类型
        :param parents: 父事件 ID 列表
        :param message: 事件消息
        :param payload: 事件载荷，支持 dict 或 list
        :return: 新事件 ID
        """
        if self.transport == "grpc":
            return self.emit_grpc(type_, parents, message, payload)
        return self.emit_http(type_, parents, message, payload)

    def emit_http(
        self,
        type_: str,
        parents: Optional[list[int]] = None,
        message: Optional[str] = None,
        payload: Optional[list[Any] | dict[str, Any]] = None,
    ) -> int:
        """
        通过 HTTP 发射一个新事件到 CelestialTree。

        :param type_: 事件类型
        :param parents: 父事件 ID 列表
        :param message: 事件消息
        :param payload: 事件载荷，支持 dict 或 list
        :return: 新事件 ID
        """
        self.init_session()

        body: dict[str, Any] = {
            "type": type_,
            "parents": parents or [],
        }

        if message is not None:
            body["message"] = message

        if payload is not None:
            body["payload"] = payload

        r = self.session.post(
            f"{self.http_addr}/emit",
            json=body,
            timeout=self.timeout,
        )

        self.raise_for_status(r)
        return r.json()["id"]

    def emit_grpc(
        self,
        type_: str,
        parents: Optional[list[int]] = None,
        message: Optional[str] = None,
        payload: Optional[list[Any] | dict[str, Any]] = None,
    ) -> int:
        """
        通过 gRPC 发射一个新事件到 CelestialTree。

        :param type_: 事件类型
        :param parents: 父事件 ID 列表
        :param message: 事件消息
        :param payload: 事件载荷，支持 dict 或 list
        :return: 新事件 ID
        """
        self.init_grpc()

        req = pb2.EmitRequest(  # type: ignore[attr-defined]
            type=type_,
            message=message or "",
            parents=parents or [],
        )

        if payload is not None:
            # proto field is google.protobuf.Struct (object). Struct 本身不支持 list 作为根。
            # 所以：dict 直接塞；list 根的话用 {"_": payload} 包一层（服务端再原样存 JSON）
            payload_dict: dict[str, Any] = {"_": payload} if isinstance(payload, list) else payload

            st = Struct()
            json_format.ParseDict(payload_dict, st)
            req.payload.CopyFrom(st)  # type: ignore[union-attr]

        try:
            resp = self.grpc_stub.Emit(req, timeout=self.timeout)  # type: ignore[union-attr]
        except grpc.RpcError as e:
            raise RuntimeError(
                f"grpc emit failed: {e.code().name}: {e.details()}"
            ) from e

        return int(resp.id)  # type: ignore[union-attr]

    def get_event(self, event_id: int) -> dict[str, Any]:
        """
        获取指定事件的详细信息。

        :param event_id: 事件 ID
        :return: 事件详情字典
        """
        self.init_session()

        r = self.session.get(
            f"{self.http_addr}/event/{event_id}",
            timeout=self.timeout,
        )

        self.raise_for_status(r)
        return r.json()

    def children(self, event_id: int) -> list[int]:
        """
        获取指定事件的直接子事件 ID 列表。

        :param event_id: 事件 ID
        :return: 子事件 ID 列表
        """
        self.init_session()

        r = self.session.get(
            f"{self.http_addr}/children/{event_id}",
            timeout=self.timeout,
        )

        self.raise_for_status(r)
        return r.json()

    def ancestors(self, event_id: int) -> list[int]:
        """
        获取指定事件的所有祖先事件 ID 列表。

        :param event_id: 事件 ID
        :return: 祖先事件 ID 列表
        """
        self.init_session()

        r = self.session.get(
            f"{self.http_addr}/ancestors/{event_id}",
            timeout=self.timeout,
        )

        self.raise_for_status(r)
        return r.json()

    def descendants(self, event_id: int, view: str = "struct") -> dict[str, Any]:
        """
        获取指定事件的后代树。

        :param event_id: 事件 ID
        :param view: 视图格式，"struct" 或 "meta"
        :return: 后代树结构
        """
        self.init_session()

        params = None
        if view and view != "struct":
            # 默认 struct 不传参，保持最干净也最兼容
            params = {"view": view}

        r = self.session.get(
            f"{self.http_addr}/descendants/{event_id}",
            params=params,
            timeout=self.timeout,
        )

        self.raise_for_status(r)
        return r.json()

    def descendants_batch(
        self, event_ids: list[int], view: str = "struct"
    ) -> list[dict[str, Any]]:
        """
        批量获取多个事件的后代树。

        :param event_ids: 事件 ID 列表
        :param view: 视图格式，"struct" 或 "meta"
        :return: 后代树列表
        """
        self.init_session()

        if not event_ids:
            raise ValueError("event_ids is required")

        body: dict[str, Any] = {"ids": event_ids}
        if view and view != "struct":
            body["view"] = view

        r = self.session.post(
            f"{self.http_addr}/descendants",
            data=json.dumps(body),
            timeout=self.timeout,
        )

        self.raise_for_status(r)
        return r.json()

    def provenance(self, event_id: int, view: str = "struct") -> dict[str, Any]:
        """
        获取指定事件的溯源树（父链）。

        :param event_id: 事件 ID
        :param view: 视图格式，"struct" 或 "meta"
        :return: 溯源树结构
        """
        self.init_session()

        params = None
        if view and view != "struct":
            params = {"view": view}

        r = self.session.get(
            f"{self.http_addr}/provenance/{event_id}",
            params=params,
            timeout=self.timeout,
        )

        self.raise_for_status(r)
        return r.json()

    def provenance_batch(
        self, event_ids: list[int], view: str = "struct"
    ) -> list[dict[str, Any]]:
        """
        批量获取多个事件的溯源树。

        :param event_ids: 事件 ID 列表
        :param view: 视图格式，"struct" 或 "meta"
        :return: 溯源树列表
        """
        self.init_session()

        if not event_ids:
            raise ValueError("event_ids is required")

        body: dict[str, Any] = {"ids": event_ids}
        if view and view != "struct":
            body["view"] = view

        r = self.session.post(
            f"{self.http_addr}/provenance",
            data=json.dumps(body),
            timeout=self.timeout,
        )

        self.raise_for_status(r)
        return r.json()
    
    def roots(self) -> list[int]:
        """
        获取所有根事件（无父节点）的 ID 列表。

        :return: 根事件 ID 列表
        """
        self.init_session()

        r = self.session.get(
            f"{self.http_addr}/roots",
            timeout=self.timeout,
        )

        self.raise_for_status(r)
        return r.json()

    def heads(self) -> list[int]:
        """
        获取所有叶子事件（无子节点）的 ID 列表。

        :return: 叶子事件 ID 列表
        """
        self.init_session()

        r = self.session.get(
            f"{self.http_addr}/heads",
            timeout=self.timeout,
        )

        self.raise_for_status(r)
        return r.json()
    
    def snapshot(self) -> dict[str, Any]:
        """
        获取当前事件图的快照。

        :return: 快照数据
        """
        self.init_session()

        r = self.session.get(
            f"{self.http_addr}/snapshot",
            timeout=self.timeout,
        )

        self.raise_for_status(r)
        return r.json()

    def health(self) -> bool:
        """
        检查服务健康状态。

        :return: 服务是否健康
        """
        self.init_session()
        try:
            r = self.session.get(
                f"{self.http_addr}/healthz",
                timeout=self.timeout,
            )
            return r.status_code == 200
        except Exception:
            return False

    def version(self) -> dict[str, Any]:
        """
        获取服务版本信息。

        :return: 版本信息字典
        """
        self.init_session()

        r = self.session.get(
            f"{self.http_addr}/version",
            timeout=self.timeout,
        )

        self.raise_for_status(r)
        return r.json()

    # ---------- SSE Subscribe ----------

    def subscribe(
        self,
        on_event: Callable[[dict[str, Any]], None],
        daemon: bool = True,
    ) -> threading.Thread:
        """
        订阅 SSE 事件流，每个事件触发 on_event 回调。

        :param on_event: 事件回调函数，接收事件字典
        :param daemon: 是否设置为守护线程
        :return: 监听线程
        """

        def _run():
            with self.session.get(
                f"{self.http_addr}/subscribe",
                stream=True,
                timeout=None,
            ) as r:
                r.raise_for_status()
                for line in r.iter_lines(decode_unicode=True):
                    if not line:
                        continue

                    if line.startswith("data:"):
                        data = line[len("data:") :].strip()
                        try:
                            ev = json.loads(data)
                            on_event(ev)
                        except Exception:
                            pass

        self.init_session()

        t = threading.Thread(target=_run, daemon=daemon)
        t.start()
        return t
