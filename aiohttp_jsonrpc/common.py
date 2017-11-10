import base64
import logging
from datetime import datetime
from functools import singledispatch
from types import GeneratorType


NoneType = type(None)

log = logging.getLogger(__name__)


class Binary(bytes):
    @classmethod
    def fromstring(cls, data):
        return cls(base64.b64decode(data))


@singledispatch
def py2json(value):
    raise TypeError(("Can't serialise type: {0}."
                    " Add type {0} via decorator "
                     "@py2json.register({0}) ").format(type(value)))


@py2json.register(bytes)
def _(value):
    return value.decode()


@py2json.register(str)
@py2json.register(float)
@py2json.register(int)
@py2json.register(bool)
@py2json.register(NoneType)
def _(value):
    return value


@py2json.register(datetime)
def _(value: datetime):
    return value.isoformat()


@py2json.register(Binary)
def _(value):
    return {
        'type': 'binary',
        'encoding': 'base64',
        'data': base64.b64encode(value)
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


__all__ = 'py2json',
