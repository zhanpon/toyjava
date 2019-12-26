from dataclasses import dataclass
from io import BytesIO
from typing import Tuple, BinaryIO, Iterable


@dataclass
class Getstatic:
    """
    https://docs.oracle.com/javase/specs/jvms/se13/html/jvms-6.html#jvms-6.5.getstatic
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
class IconstM1:
    CODE = b"\x02"


@dataclass
class Iconst0:
    CODE = b"\x03"


@dataclass
class Iconst1:
    CODE = b"\x04"


@dataclass
class Iconst2:
    CODE = b"\x05"


@dataclass
class Iconst3:
    CODE = b"\x06"


@dataclass
class Iconst4:
    CODE = b"\x07"


@dataclass
class Iconst5:
    CODE = b"\x08"


@dataclass
class Istore1:
    CODE = b"<"


@dataclass
class Istore2:
    CODE = b"="


@dataclass
class Iload1:
    CODE = b"\x1b"


@dataclass
class Iload2:
    CODE = b"\x1c"


@dataclass
class RawIfIcmpge:
    CODE = b"\xa2"
    branchbyte: int


@dataclass
class Iinc:
    CODE = b"\x84"
    index: int
    const: int


@dataclass
class RawGoto:
    CODE = b"\xa7"
    branchbyte: int


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
            elif code == IconstM1.CODE:
                yield IconstM1()
            elif code == Iconst0.CODE:
                yield Iconst0()
            elif code == Iconst1.CODE:
                yield Iconst1()
            elif code == Iconst2.CODE:
                yield Iconst2()
            elif code == Iconst3.CODE:
                yield Iconst3()
            elif code == Iconst4.CODE:
                yield Iconst4()
            elif code == Iconst5.CODE:
                yield Iconst5()
            elif code == Istore1.CODE:
                yield Istore1()
            elif code == Istore2.CODE:
                yield Istore2()
            elif code == Iload1.CODE:
                yield Iload1()
            elif code == Iload2.CODE:
                yield Iload2()
            elif code == RawIfIcmpge.CODE:
                branchbyte = self._read_index(2)
                yield RawIfIcmpge(branchbyte)
            elif code == Iinc.CODE:
                yield Iinc(self._read_index(1), self._read_index(1))
            elif code == RawGoto.CODE:
                b = self.stream.read(2)
                yield RawGoto(int.from_bytes(b, "big", signed=True))
            else:
                raise NotImplementedError(code)

    def read(self):
        raw_instructions = []
        positions = [0]
        for raw_instruction in self._read():
            raw_instructions.append(raw_instruction)
            positions.append(self.stream.tell())

        positions.pop()

        return tuple(raw_instructions), positions


@dataclass
class IfIcmpge:
    index: int


@dataclass
class Goto:
    index: int


def convert(instructions, positions: list):
    for pos, instruction in zip(positions, instructions):
        if isinstance(instruction, RawIfIcmpge):
            branchbyte = pos + instruction.branchbyte
            index = positions.index(branchbyte)
            yield IfIcmpge(index)
        elif isinstance(instruction, RawGoto):
            branchbyte = pos + instruction.branchbyte
            index = positions.index(branchbyte)
            yield Goto(index)
        else:
            yield instruction


def parse_instructions(code: bytes) -> Tuple:
    reader = InstructionReader(BytesIO(code))
    instructions, positions = reader.read()
    return tuple(convert(instructions, positions))
