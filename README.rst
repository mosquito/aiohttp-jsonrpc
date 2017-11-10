AIOHTTP JSON RPC
================

.. image:: https://travis-ci.org/mosquito/aiohttp-jsonrpc.svg
    :target: https://travis-ci.org/mosquito/aiohttp-jsonrpc

.. image:: https://img.shields.io/pypi/v/aiohttp-jsonrpc.svg
    :target: https://pypi.python.org/pypi/aiohttp-jsonrpc/
    :alt: Latest Version

.. image:: https://img.shields.io/pypi/wheel/aiohttp-jsonrpc.svg
    :target: https://pypi.python.org/pypi/aiohttp-jsonrpc/

.. image:: https://img.shields.io/pypi/pyversions/aiohttp-jsonrpc.svg
    :target: https://pypi.python.org/pypi/aiohttp-jsonrpc/

.. image:: https://img.shields.io/pypi/l/aiohttp-jsonrpc.svg
    :target: https://pypi.python.org/pypi/aiohttp-jsonrpc/


JSON-RPC server and client implementation based on aiohttp.


Server example
---------------

.. code-block:: python

    from aiohttp import web
    from aiohttp_jsonrpc import handler


    class JSONRPCExample(handler.JSONRPCView):
        def rpc_test(self):
            return None

        def rpc_args(self, *args):
            return len(args)

        def rpc_kwargs(self, **kwargs):
            return len(kwargs)

        def rpc_args_kwargs(self, *args, **kwargs):
            return len(args) + len(kwargs)

        def rpc_exception(self):
            raise Exception("YEEEEEE!!!")


    app = web.Application()
    app.router.add_route('*', '/', JSONRPCExample)

    if __name__ == "__main__":
        import logging
        logging.basicConfig(level=logging.INFO)
        web.run_app(app, print=logging.info)



Client example
--------------

.. code-block:: python

    import asyncio
    from aiohttp_jsonrpc.client import ServerProxy, batch


    loop = asyncio.get_event_loop()
    client = ServerProxy("http://127.0.0.1:8080/", loop=loop)


    async def main():
        print(await client.test())

        # Or via __getitem__
        method = client['args']
        print(await method(1, 2, 3))

        results = await batch(
            client,
            client['test'],
            client['test'].prepare(),
            client['args'].prepare(1, 2, 3),
            client['not_found'].prepare(1, 2, 3),
        )

        print(results)

        client.close()

    if __name__ == "__main__":
        loop.run_until_complete(main())

