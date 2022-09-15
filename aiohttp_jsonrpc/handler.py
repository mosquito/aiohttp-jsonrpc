import asyncio
import json
import logging
from typing import Union

from aiohttp.web import HTTPBadRequest, Response, View

from . import exceptions
from .common import (
    JSONRPCBody, JSONRPCRequest, JSONRPCResponse, awaitable, py2json,
)


log = logging.getLogger(__name__)


class JSONRPCView(View):
    METHOD_PREFIX = "rpc_"

    DUMPS = json.dumps
    LOADS = json.loads

    async def post(self):
        await self.authorize()

        body: bytes = await self.request.read()
        json_request: JSONRPCBody = self._parse_body(body)
        batch_mode = False

        if isinstance(json_request, dict):
            requests = [json_request]
        elif isinstance(json_request, list):
            requests = json_request
            batch_mode = True
        else:
            raise HTTPBadRequest

        results = await asyncio.gather(
            *[self._handle(request) for request in requests]
        )

        if batch_mode:
            return self._make_response(list(filter(None, results)))
        else:
            return self._make_response(results[0])

    @classmethod
    def _make_response(cls, json_response, status: int = None, reason=None):
        log.debug("Sending response:\n%r", json_response)

        if json_response is None:
            return Response(
                status=status or 204,
                reason=reason,
                body=b"",
            )

        return Response(
            status=status or 200,
            reason=reason,
            body=cls._build_json(json_response),
            headers={"Content-Type": "application/json; charset=utf-8"},
        )

    def _parse_body(self, body) -> JSONRPCBody:
        try:
            return self._parse_json(body)
        except ValueError:
            raise HTTPBadRequest

    def _lookup_method(self, method_name):
        method = getattr(
            self, "{0}{1}".format(self.METHOD_PREFIX, method_name), None,
        )

        if not callable(method):
            log.warning(
                "Can't find method %s%s in %r",
                self.METHOD_PREFIX,
                method_name,
                self.__class__.__name__,
            )

            raise exceptions.ApplicationError(
                "Method %r not found" % method_name,
            )
        return method

    async def authorize(self):
        if "json" not in self.request.headers.get("Content-Type", ""):
            raise HTTPBadRequest

    async def _handle(self, json_request: JSONRPCRequest):
        request_id = json_request.get("id")

        try:
            method_name = json_request["method"]
            method = self._lookup_method(method_name)

            log.info(
                "RPC Call: %s => %s.%s.%s",
                method_name,
                method.__module__,
                method.__class__.__name__,
                method.__name__,
            )

            params = json_request.get("params")

            args = []
            kwargs = {}

            if isinstance(params, list):
                args = params
            elif isinstance(params, dict):
                kwargs = params

            result = await awaitable(method)(*args, **kwargs)

            if "id" not in json_request:
                return None

            return self._format_success(result, request_id)
        except Exception as e:
            return self._format_error(e, request_id)

    @staticmethod
    def _format_success(result, request_id: Union[str, int]):
        return JSONRPCResponse(
            jsonrpc="2.0",
            id=request_id,
            result=result,
        )

    @staticmethod
    def _format_error(
        exception: Exception, request_id: Union[str, int],
    ) -> JSONRPCResponse:
        return JSONRPCResponse(
            jsonrpc="2.0",
            id=request_id,
            error=py2json(exception),
        )

    @classmethod
    def _parse_json(cls, json_string):
        return cls.LOADS(json_string.decode())

    @classmethod
    def _build_json(cls, data):
        return cls.DUMPS(py2json(data), ensure_ascii=False)
