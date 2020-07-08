import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer, TestClient

from aiohttp_jsonrpc.client import ServerProxy
from aiohttp_jsonrpc.handler import JSONRPCView


class CustomServerException(Exception):
    code = 5001


class CustomClientException(Exception):
    code = 5001


class JSONRPCTestService(JSONRPCView):
    __JSONRPC_EXCEPTIONS__ = {
        CustomServerException: CustomServerException.code
    }

    def rpc_echo_exception(self, message):
        raise CustomServerException(message)


class CustomServerProxy(ServerProxy):
    __JSONRPC_EXCEPTIONS__ = {
        CustomClientException.code: CustomClientException
    }


def create_app():
    app = web.Application()
    app.router.add_route("*", "/", JSONRPCTestService)
    return app


@pytest.fixture
def custom_jsonrpc_test_client(add_cleanup):
    test_client = None
    rpc_client = None

    async def _create_from_app_factory(app_factory, *args, **kwargs):
        nonlocal test_client, rpc_client

        app = app_factory(*args, **kwargs)
        test_client = TestClient(TestServer(app))

        await test_client.start_server()

        rpc_client = CustomServerProxy("", client=test_client)

        add_cleanup(rpc_client.close)
        add_cleanup(test_client.close)

        return rpc_client

    return _create_from_app_factory


@pytest.fixture
async def custom_client(loop, custom_jsonrpc_test_client):
    return await custom_jsonrpc_test_client(create_app)


async def test_custom_handler_exception(custom_client):
    """
    This test shows that server raises CustomServerException
    and CustomServerProxy re-raises exception CustomClientException,
    which is defined in it's __JSONRPC_EXCEPTIONS__ dict.
    """
    with pytest.raises(CustomClientException) as exc_info:
        await custom_client.echo_exception('My message')

    assert exc_info.value.args[0] == 'My message'
