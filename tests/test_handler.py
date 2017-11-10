import asyncio

import pytest
from aiohttp import web
from aiohttp_jsonrpc import handler
from aiohttp_jsonrpc.client import batch
from aiohttp_jsonrpc.exceptions import ApplicationError


pytest_plugins = (
    'aiohttp.pytest_plugin',
    'aiohttp_jsonrpc.pytest_plugin',
)


class JSONRPCMain(handler.JSONRPCView):
    def rpc_test(self):
        return None

    def rpc_args(self, *args):
        return len(args)

    def rpc_kwargs(self, **kwargs):
        return len(kwargs)

    def rpc_exception(self):
        raise Exception("YEEEEEE!!!")

    def rpc_strings(self, s1, s2):
        return s1 == s2

    def rpc_mirror(self, arg):
        return arg


def create_app(loop):
    app = web.Application(loop=loop)
    app.router.add_route('*', '/', JSONRPCMain)
    return app


@pytest.fixture
def client(loop, test_rpc_client):
    return loop.run_until_complete(test_rpc_client(create_app))


@asyncio.coroutine
def test_1_test(client):
    result = yield from client.test()
    assert result is None


@asyncio.coroutine
def test_2_args(client):
    result = yield from client.args(1, 2, 3, 4, 5)
    assert result == 5


@asyncio.coroutine
def test_3_kwargs(client):
    result = yield from client.kwargs(foo=1, bar=2)
    assert result == 2


@asyncio.coroutine
def test_5_exception(client):
    with pytest.raises(Exception):
        yield from client.exception()


@asyncio.coroutine
def test_6_unknown_method(client):
    with pytest.raises(ApplicationError):
        yield from client['unknown_method']()


@asyncio.coroutine
def test_7_batch(client):
    results = yield from batch(
        client,
        client.mirror.prepare(0),
        client.mirror.prepare(1),
        client.mirror.prepare(2),
        client.mirror.prepare(3),
        client.mirror.prepare(4),
        client.mirror.prepare(5),
        client.mirror.prepare(6),
        client.mirror.prepare(7),
        client.mirror.prepare(8),
        client.mirror.prepare(9),
    )

    assert results == list(range(10))
