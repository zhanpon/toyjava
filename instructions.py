from dataclasses import dataclass
from typing import Tuple, BinaryIO, Iterable
from io import BytesIO


@dataclass
class Getstatic:
    """
    https://docs.oracle.com/javase/specs/jvms/se11/html/jvms-6.html#jvms-6.5.getstatic
    """

    CODE = b"\xb2"
    index: int


@dataclass
class Ldc:
    CODE = b"\x12"
    index: int


@dataclass
class Invokevirtual:
    CODE = b"\xb6"
    index: int


@dataclass
class Return:
    CODE = b"\xb1"


@dataclass
class Iconst2:
    CODE = b"\x05"


class InstructionReader:
    def __init__(self, stream: BinaryIO):
        self.stream = stream

    def _read_index(self, bytes_length: int) -> int:
        return int.from_bytes(self.stream.read(bytes_length), "big")

    def _read(self) -> Iterable:
        while True:
            code = self.stream.read(1)
            if code == b"":
                break
            elif code == Getstatic.CODE:
                yield Getstatic(self._read_index(2))
            elif code == Ldc.CODE:
                yield Ldc(self._read_index(1))
            elif code == Invokevirtual.CODE:
                yield Invokevirtual(self._read_index(2))
            elif code == Return.CODE:
                yield Return()
            elif code == Iconst2.CODE:
                yield Iconst2()
            else:
                raise NotImplementedError(code)

    def read(self):
        return tuple(self._read())


def parse_instructions(code: bytes) -> Tuple:
    reader = InstructionReader(BytesIO(code))
    return reader.read()
