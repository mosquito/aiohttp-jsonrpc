import asyncio
import base64
import logging
import typing
from datetime import datetime
from functools import singledispatch, wraps
from types import GeneratorType


try:
    from typing import TypedDict
except ImportError:
    from typing_extensions import TypedDict


log = logging.getLogger(__name__)


class JSONRPCRequest(TypedDict, total=False):
    jsonrpc: str
    id: typing.Union[int, str, None]
    method: str
    params: typing.Union[
        typing.Sequence[typing.Any], typing.Mapping[str, typing.Any],
    ]


class JSONRPCError(TypedDict, total=False):
    code: int
    message: str
    data: typing.Any


class JSONRPCResponse(TypedDict, total=False):
    jsonrpc: str
    id: typing.Union[int, str, None]
    result: typing.Any
    error: JSONRPCError


class Binary(bytes):
    @classmethod
    def fromstring(cls, data):
        return cls(base64.b64decode(data))


@singledispatch
def py2json(value):
    raise TypeError((
        "Can't serialise type: {0}."
        " Add type {0} via decorator "
        "@py2json.register({0})"
    ).format(type(value)))


@py2json.register(bytes)
def _(value):
    return value.decode()


@py2json.register(str)
@py2json.register(float)
@py2json.register(int)
@py2json.register(bool)
@py2json.register(type(None))
def _(value):
    return value


@py2json.register(datetime)
def _(value: datetime):
    return value.isoformat()


@py2json.register(Binary)
def _(value):
    return {
        "type": "binary",
        "encoding": "base64",
        "data": base64.b64encode(value),
    }


@py2json.register(list)
@py2json.register(tuple)
@py2json.register(set)
@py2json.register(frozenset)
@py2json.register(GeneratorType)
def _(x):
    return [py2json(i) for i in x]


@py2json.register(dict)
def _(x):
    return {str(key): py2json(value) for key, value in x.items()}


@py2json.register(BaseException)
def _(e: BaseException) -> JSONRPCError:
    return JSONRPCError(
        message=str(e),
        data=py2json(getattr(e, "args", None)),
    )


def awaitable(func):
    # Avoid python 3.8+ warning
    if asyncio.iscoroutinefunction(func):
        return func

    async def awaiter(obj):
        return obj

    @wraps(func)
    def wrap(*args, **kwargs):
        result = func(*args, **kwargs)

        if hasattr(result, "__await__"):
            return result
        if asyncio.iscoroutine(result) or asyncio.isfuture(result):
            return result

        return awaiter(result)

    return wrap


JSONRPCBatchRequest = typing.List[JSONRPCRequest]
JSONRPCBody = typing.Union[JSONRPCRequest, JSONRPCBatchRequest]


__all__ = (
    "JSONRPCBatchRequest",
    "JSONRPCError",
    "JSONRPCRequest",
    "JSONRPCResponse",
    "py2json",
)
