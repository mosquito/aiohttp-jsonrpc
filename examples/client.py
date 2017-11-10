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
