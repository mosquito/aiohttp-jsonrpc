from functools import partial

import pytest
from aiohttp.test_utils import TestClient, TestServer

from aiohttp_jsonrpc.client import ServerProxy


@pytest.fixture
def add_cleanup(loop):
    cleanups = []

    def payload(func, *args, **kwargs):
        nonlocal cleanups
        func = partial(func, *args, **kwargs)
        cleanups.append(func)

    try:
        yield payload
    finally:
        for func in cleanups[::-1]:
            loop.run_until_complete(func())

        cleanups.clear()


@pytest.fixture
def jsonrpc_test_client(add_cleanup):
    test_client = None
    rpc_client = None

    async def _create_from_app_factory(app_factory, *args, **kwargs):
        nonlocal test_client, rpc_client

        app = app_factory(*args, **kwargs)
        test_client = TestClient(TestServer(app))

        await test_client.start_server()

        rpc_client = ServerProxy("", client=test_client)

        add_cleanup(rpc_client.close)
        add_cleanup(test_client.close)

        return rpc_client

    return _create_from_app_factory
