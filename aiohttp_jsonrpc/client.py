import asyncio
import json
import logging
import uuid
from typing import Any, Dict, Iterable, List, Tuple, Union

import aiohttp.client
import aiohttp.test_utils
import yarl
from multidict import CIMultiDict, MultiDict

from . import __pyversion__, __version__, exceptions
from .common import JSONRPCBody, JSONRPCRequest, py2json
from .exceptions import json2py_exception


log = logging.getLogger(__name__)


class Method:
    def __init__(self, name, execute):
        self.name = name
        self.execute = execute

    def __call__(self, *args, **kwargs):
        return self.execute(self.prepare(*args, **kwargs))

    def prepare(self, *args, **kwargs) -> JSONRPCRequest:
        return JSONRPCRequest(
            id=str(uuid.uuid4()),
            method=str(self.name),
            jsonrpc="2.0",
            params=args if args else kwargs,
        )


class Notification(Method):
    def _create_request(self) -> JSONRPCRequest:
        return JSONRPCRequest(
            jsonrpc="2.0",
            method=str(self.name),
        )


HeadersType = Union[
    CIMultiDict,
    Dict[str, str],
    Iterable[Tuple[str, str]],
]

ClientSessionType = Union[
    aiohttp.client.ClientSession,
    aiohttp.test_utils.TestClient,
]


class ServerProxy(object):
    __slots__ = (
        "client", "url", "loop", "headers", "loads", "dumps", "client_owner",
    )

    USER_AGENT = "aiohttp JSON-RPC client (Python: {0}, version: {1})".format(
        __pyversion__, __version__,
    )

    def __init__(
        self, url: Union[str, yarl.URL],
        client: ClientSessionType = None,
        loop: asyncio.AbstractEventLoop = None,
        headers: HeadersType = None,
        client_owner: bool = True,
        loads=json.loads,
        dumps=json.dumps,
        **kwargs,
    ):

        self.headers = MultiDict(headers or {})
        self.headers.setdefault("Content-Type", "application/json")
        self.headers.setdefault("User-Agent", self.USER_AGENT)

        self.url = str(url)
        self.loop = loop or asyncio.get_event_loop()
        self.client = client or aiohttp.client.ClientSession(
            loop=self.loop, **kwargs
        )
        self.client_owner = bool(client_owner)

        self.loads = loads
        self.dumps = dumps

    @staticmethod
    def _parse_response(response):
        log.debug("Server response: \n%r", response)

        if "error" in response:
            error = response["error"]

            if not isinstance(error, dict):
                raise Exception
            else:
                raise json2py_exception(
                    error.get("code", exceptions.SystemError.code),
                    error.get("message", "Unknown error"),
                    default_exc_class=exceptions.ServerError,
                )
        return response.get("result")

    async def __remote_call(self, json_request: JSONRPCRequest) -> Any:
        request = py2json(json_request)
        response = await self.client.post(
            str(self.url),
            headers=await self.prepare_headers(self.headers),
            data=self.dumps(
                await self.prepare_body(py2json(request)),
            ),
        )

        response.raise_for_status()

        if "id" not in request:
            # Notification
            return

        return self._parse_response(
            self.loads((await response.read()).decode()),
        )

    async def prepare_headers(self, headers: MultiDict) -> MultiDict:
        return headers

    async def prepare_body(
        self, body: Union[JSONRPCRequest, JSONRPCBody],
    ) -> JSONRPCBody:
        return body

    async def __call__(
        self, *prepared_methods: JSONRPCRequest, return_exceptions=True
    ) -> Any:
        request = []
        request_indecies = []

        for req in prepared_methods:
            if isinstance(req, Method):
                req = req.prepare()

            if isinstance(req, Notification):
                req = req.prepare()

            request_indecies.append(req.get("id"))
            request.append(req)

        response = await self.client.post(
            str(self.url),
            headers=await self.prepare_headers(self.headers),
            data=self.dumps(
                await self.prepare_body(py2json(request)),
            ),
        )

        response.raise_for_status()

        responses: Dict[Any, Any] = {}
        data: List[JSONRPCRequest] = self.loads(
            (await response.read()).decode(),
        )

        for response in data:
            req_id = response.get("id")
            if not req_id:
                continue

            try:
                responses[req_id] = self._parse_response(response)
            except Exception as e:
                if return_exceptions:
                    responses[req_id] = e
                    continue
                raise

        result = []
        for req_id in request_indecies:
            if req_id is None:
                result.append(None)
                continue

            result.append(responses[req_id])
        return result

    def __getattr__(self, method_name: str) -> Method:
        return self[method_name]

    def __getitem__(self, method_name: str) -> Method:
        return Method(method_name, self.__remote_call)

    def create_notification(self, method: str):
        return Notification(method, self.__remote_call)

    async def close(self, force=False):
        if not self.client_owner and not force:
            return
        return await self.client.close()

    async def __aenter__(self) -> "ServerProxy":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client.closed:
            return
        await self.close()
