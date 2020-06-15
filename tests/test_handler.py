import pytest
from aiohttp import web

from aiohttp_jsonrpc import handler
from aiohttp_jsonrpc.client import ServerProxy, batch
from aiohttp_jsonrpc.exceptions import ApplicationError


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


def create_app():
    app = web.Application()
    app.router.add_route("*", "/", JSONRPCMain)
    return app


@pytest.fixture
async def client(loop, jsonrpc_test_client):
    return await jsonrpc_test_client(create_app)


async def test_1_test(client: ServerProxy):
    result = await client.test()
    assert result is None


async def test_2_args(client: ServerProxy):
    result = await client.args(1, 2, 3, 4, 5)
    assert result == 5


async def test_3_kwargs(client: ServerProxy):
    result = await client.kwargs(foo=1, bar=2)
    assert result == 2


async def test_5_exception(client: ServerProxy):
    with pytest.raises(Exception):
        await client.exception()


async def test_6_unknown_method(client: ServerProxy):
    with pytest.raises(ApplicationError):
        await client["unknown_method"]()


async def test_7_batch(client: ServerProxy):
    results = await batch(
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


async def test_7_batch_method(client: ServerProxy):
    results = await client(
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


async def test_8_notification(client: ServerProxy):
    notification = client.create_notification("test")
    await notification()


async def test_9_batch_method_and_notifications(client: ServerProxy):
    notification = client.create_notification("test")

    results = await client(
        client.mirror.prepare(0),
        client.mirror.prepare(1),
        notification,
        client.mirror.prepare(2),
        client.mirror.prepare(3),
        client.test,
        notification.prepare(),
    )

    assert results == [0, 1, None, 2, 3, None, None]
