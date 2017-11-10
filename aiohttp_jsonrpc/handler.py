# encoding: utf-8
import json
import logging
import asyncio
from aiohttp.web import View, Response, HTTPBadRequest
from . import exceptions
from .common import py2json


log = logging.getLogger(__name__)


class JSONRPCView(View):
    METHOD_PREFIX = "rpc_"

    DUMPS = json.dumps
    LOADS = json.loads

    @asyncio.coroutine
    def post(self, *args, **kwargs):
        self._check_request()

        body = yield from self.request.read()
        json_request = self._parse_body(body)
        batch_mode = False

        if isinstance(json_request, dict):
            requests = [json_request]
        elif isinstance(json_request, list):
            requests = json_request
            batch_mode = True
        else:
            raise HTTPBadRequest

        results = yield from asyncio.gather(*[self._handle(request) for request in requests])

        if batch_mode:
            return self._make_response(results)
        else:
            return self._make_response(results[0])

    @classmethod
    def _make_response(cls, json_response, status=200, reason=None):
        log.debug("Sending response:\n%r", json_response)
        return Response(
            status=status,
            reason=reason,
            body=cls._build_json(json_response),
            headers={"Content-Type": "application/json; charset=utf-8"}
        )

    def _parse_body(self, body):
        try:
            return self._parse_json(body)
        except ValueError:
            raise HTTPBadRequest

    def _lookup_method(self, method_name):
        method = getattr(self, "{0}{1}".format(self.METHOD_PREFIX, method_name), None)

        if not callable(method):
            log.warning(
                "Can't find method %s%s in %r",
                self.METHOD_PREFIX,
                method_name,
                self.__class__.__name__
            )

            raise exceptions.ApplicationError('Method %r not found' % method_name)
        return method

    def _check_request(self):
        if 'json' not in self.request.headers.get('Content-Type', ''):
            raise HTTPBadRequest

    @asyncio.coroutine
    def _handle(self, json_request):
        request_id = json_request.get('id')

        try:
            method_name = json_request['method']
            method = self._lookup_method(method_name)

            log.info(
                "RPC Call: %s => %s.%s.%s",
                method_name,
                method.__module__,
                method.__class__.__name__,
                method.__name__
            )

            params = json_request.get('params')

            args = []
            kwargs = {}

            if isinstance(params, list):
                args = params
            elif isinstance(params, dict):
                kwargs = params

            result = yield from asyncio.coroutine(method)(*args, **kwargs)
            return self._format_success(result, request_id)
        except Exception as e:
            return self._format_error(e, request_id)

    @staticmethod
    def _format_success(result, request_id):
        data = {"jsonrpc": "2.0"}

        if result is not None:
            data['result'] = result
        if request_id is not None:
            data['id'] = request_id

        return data

    @staticmethod
    def _format_error(exception: Exception, request_id):
        data = {
            "jsonrpc": "2.0",
            "error": exception,
        }

        if request_id is not None:
            data['id'] = request_id

        return data

    @classmethod
    def _parse_json(cls, json_string):
        return cls.LOADS(json_string.decode())

    @classmethod
    def _build_json(cls, data):
        return cls.DUMPS(py2json(data), ensure_ascii=False)
