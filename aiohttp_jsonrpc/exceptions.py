from .common import py2json


__all__ = (
    'JSONRPCError', 'ApplicationError', 'InvalidCharacterError',
    'ParseError', 'ServerError', 'SystemError', 'TransportError',
    'UnsupportedEncodingError',
)


class JSONRPCError(Exception):
    code = -32500

    @property
    def message(self):
        return self.args[0]

    @property
    def name(self):
        return self.__class__.__name__

    def __repr__(self):
        return '<[{0.code}] {0.name}({0.message})>'.format(self)


class ParseError(JSONRPCError):
    code = -32700


class UnsupportedEncodingError(ParseError):
    code = -32701


class InvalidCharacterError(ParseError):
    code = -32702


class ServerError(JSONRPCError):
    code = -32603


class InvalidData(ServerError):
    code = -32600


class MethodNotFound(ServerError):
    code = -32601


class InvalidArguments(ServerError):
    code = -32602


class ApplicationError(JSONRPCError):
    code = -32500


class SystemError(JSONRPCError):
    code = -32400


class TransportError(JSONRPCError):
    code = -32300


__EXCEPTION_CODES = {
    -32000: Exception,
    JSONRPCError.code: JSONRPCError,
    ParseError.code: ParseError,
    UnsupportedEncodingError.code: UnsupportedEncodingError,
    InvalidCharacterError.code: InvalidCharacterError,
    ServerError.code: ServerError,
    InvalidData.code: InvalidData,
    MethodNotFound.code: MethodNotFound,
    InvalidArguments.code: InvalidArguments,
    ApplicationError.code: ApplicationError,
    SystemError.code: SystemError,
    TransportError.code: TransportError,
}

__EXCEPTION_TYPES = {value: key for key, value in __EXCEPTION_CODES.items()}


def register_exception(exception_type: BaseException, code: int):
    code = int(code)
    if not issubclass(exception_type, BaseException):
        raise TypeError("Exception must be instance of Base exception")

    if code in __EXCEPTION_CODES:
        raise ValueError("Exception with code %s already registered" % code)

    if exception_type in __EXCEPTION_TYPES:
        raise ValueError("Exception type %r already registered" % exception_type)

    __EXCEPTION_CODES[code] = exception_type
    __EXCEPTION_TYPES[exception_type] = code


def json2py_exception(code: int, fault: str, default_exc_class=JSONRPCError):
    if code not in __EXCEPTION_CODES:
        exc = default_exc_class(fault)
        exc.code = code
        return exc

    exc = __EXCEPTION_CODES[code]
    return exc(fault)


@py2json.register(Exception)
def _(value: Exception):
    code, reason = __EXCEPTION_TYPES[Exception], " ".join(map(str, value.args))

    for klass in value.__class__.__mro__:
        if klass in __EXCEPTION_TYPES:
            code = __EXCEPTION_TYPES[klass]
            break

    return {"code": code, "message": reason}
