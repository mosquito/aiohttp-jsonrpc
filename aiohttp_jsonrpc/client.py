import asyncio
import aiohttp.client
import logging
import json
from multidict import MultiDict

from . import __version__, __pyversion__, exceptions
from .exceptions import json2py_exception
from .common import py2json

log = logging.getLogger(__name__)


class Method:
    def __init__(self, name, execute):
        self.name = name
        self.execute = execute

    def __call__(self, *args, **kwargs):
        return self.execute(self.prepare(*args, **kwargs))

    def prepare(self, *args, **kwargs):
        data = {
            "method": str(self.name),
            "jsonrpc": "2.0",
        }

        if args:
            data['params'] = args

        elif kwargs:
            data['params'] = kwargs

        return data


class ServerProxy(object):
    __slots__ = 'client', 'url', 'loop', 'headers', 'loads', 'dumps'

    USER_AGENT = u'aiohttp JSON-RPC client (Python: {0}, version: {1})'.format(__pyversion__, __version__)

    def __init__(self, url, client=None, loop=None, headers=None,
                 loads=json.loads, dumps=json.dumps, **kwargs):

        self.headers = MultiDict(headers or {})

        self.headers.setdefault('Content-Type', 'application/json')
        self.headers.setdefault('User-Agent', self.USER_AGENT)

        self.url = str(url)
        self.loop = loop or asyncio.get_event_loop()
        self.client = client or aiohttp.client.ClientSession(loop=self.loop, **kwargs)

        self.loads = loads
        self.dumps = dumps

    @staticmethod
    def _parse_response(response):
        log.debug("Server response: \n%r", response)

        if 'error' in response:
            error = response['error']

            if not isinstance(error, dict):
                raise Exception
            else:
                raise json2py_exception(
                    error.get('code', exceptions.SystemError.code),
                    error.get('message', 'Unknown error'),
                    default_exc_class=exceptions.ServerError
                )
        return response.get('result')

    @asyncio.coroutine
    def __remote_call(self, json_request):
        response = yield from self.client.post(
            str(self.url),
            headers=self.headers,
            data=self.dumps(py2json(json_request)),
        )

        response.raise_for_status()

        return self._parse_response(
            self.loads((yield from response.read()).decode())
        )

    @asyncio.coroutine
    def _batch_call(self, prepared_methods):

        request = []

        for idx, req in enumerate(prepared_methods):
            if isinstance(req, Method):
                req = req.prepare()

            req['id'] = idx + 1
            request.append(req)

        response = yield from self.client.post(
            str(self.url),
            headers=self.headers,
            data=self.dumps(py2json(request)),
        )

        response.raise_for_status()

        responses = []
        data = self.loads((yield from response.read()).decode())

        for response in data:
            try:
                responses.append(self._parse_response(response))
            except Exception as e:
                responses.append(e)

        return responses

    def __getattr__(self, method_name) -> Method:
        return self[method_name]

    def __getitem__(self, method_name) -> Method:
        return Method(method_name, self.__remote_call)

    def close(self):
        return self.client.close()


def batch(server_proxy: ServerProxy, *methods):
    return server_proxy._batch_call(methods)
