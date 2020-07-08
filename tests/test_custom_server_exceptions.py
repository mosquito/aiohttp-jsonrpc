import pytest
from aiohttp import web

from aiohttp_jsonrpc.handler import JSONRPCView


class CustomServerException(Exception):
    code = 5001


class JSONRPCTestService(JSONRPCView):
    __JSONRPC_EXCEPTIONS__ = {
        CustomServerException: CustomServerException.code
    }

    def rpc_echo_exception(self, message):
        raise CustomServerException(message)


def create_app():
    app = web.Application()
    app.router.add_route("*", "/", JSONRPCTestService)
    return app


@pytest.fixture
async def client(loop, jsonrpc_test_client):
    return await jsonrpc_test_client(create_app)


async def test_custom_server_exception(client):
    """
    This test shows that server raises CustomServerException,
    which is defined in it's __JSONRPC_EXCEPTIONS__ dict,
    and client gets an exception with code of CustomServerException.
    """
    with pytest.raises(Exception) as exc_info:
        await client.echo_exception('My message')

    assert exc_info.value.args[0] == 'My message'
    assert getattr(exc_info.value, 'code') == 5001
