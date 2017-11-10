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
