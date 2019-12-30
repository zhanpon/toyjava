import operator as op
from dataclasses import dataclass
from io import BytesIO
from typing import Tuple, BinaryIO, Iterable, Callable

CODE_iconst_m1 = b"\x02"
CODE_iconst_0 = b"\x03"
CODE_iconst_1 = b"\x04"
CODE_iconst_2 = b"\x05"
CODE_iconst_3 = b"\x06"
CODE_iconst_4 = b"\x07"
CODE_iconst_5 = b"\x08"
CODE_bipush = b"\x10"
CODE_if_icmpge = b"\xa2"
CODE_if_icmpgt = b"\xa3"


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
class Ireturn:
    CODE = b"\xac"


@dataclass
class Push:
    value: int


@dataclass
class Istore1:
    CODE = b"<"


@dataclass
class Istore2:
    CODE = b"="


@dataclass
class Iload0:
    CODE = b"\x1a"


@dataclass
class Iload1:
    CODE = b"\x1b"


@dataclass
class Iload2:
    CODE = b"\x1c"


@dataclass
class UnresolvedBranchIf2:
    offset: int
    predicate: Callable[[int, int], bool]


@dataclass
class RawIfne:
    CODE = b"\x9a"
    branchbyte: int


@dataclass
class Iinc:
    CODE = b"\x84"
    index: int
    const: int


@dataclass
class Iadd:
    CODE = b'`'


@dataclass
class Irem:
    CODE = b"p"


@dataclass
class RawGoto:
    CODE = b"\xa7"
    branchbyte: int


@dataclass
class InvokeStatic:
    CODE = b"\xb8"
    index: int


class InstructionReader:
    def __init__(self, stream: BinaryIO):
        self.stream = stream

    def _read_index(self, bytes_length: int) -> int:
        return int.from_bytes(self.stream.read(bytes_length), "big")

    def _read_sint(self, bytes_length: int) -> int:
        return int.from_bytes(self.stream.read(bytes_length), "big", signed=True)

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
            elif code == InvokeStatic.CODE:
                yield InvokeStatic(self._read_index(2))
            elif code == Return.CODE:
                yield Return()
            elif code == Ireturn.CODE:
                yield Ireturn()
            elif code == CODE_iconst_m1:
                yield Push(-1)
            elif code == CODE_iconst_0:
                yield Push(0)
            elif code == CODE_iconst_1:
                yield Push(1)
            elif code == CODE_iconst_2:
                yield Push(2)
            elif code == CODE_iconst_3:
                yield Push(3)
            elif code == CODE_iconst_4:
                yield Push(4)
            elif code == CODE_iconst_5:
                yield Push(5)
            elif code == Irem.CODE:
                yield Irem()
            elif code == Iadd.CODE:
                yield Iadd()
            elif code == CODE_bipush:
                yield Push(self._read_sint(1))
            elif code == Istore1.CODE:
                yield Istore1()
            elif code == Istore2.CODE:
                yield Istore2()
            elif code == Iload0.CODE:
                yield Iload0()
            elif code == Iload1.CODE:
                yield Iload1()
            elif code == Iload2.CODE:
                yield Iload2()
            elif code == RawIfne.CODE:
                branchbyte = self._read_index(2)
                yield RawIfne(branchbyte)
            elif code == CODE_if_icmpge:
                yield UnresolvedBranchIf2(offset=self._read_sint(2), predicate=op.ge)
            elif code == CODE_if_icmpgt:
                yield UnresolvedBranchIf2(offset=self._read_sint(2), predicate=op.gt)
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
class Ifne:
    index: int


@dataclass
class BranchIf2:
    index: int
    predicate: Callable[[int, int], bool]


@dataclass
class IfIcmpge:
    index: int


@dataclass
class IfIcmpgt:
    index: int


@dataclass
class Goto:
    index: int


def convert(instructions, positions: list):
    for pos, instruction in zip(positions, instructions):
        if isinstance(instruction, RawIfne):
            branchbyte = pos + instruction.branchbyte
            index = positions.index(branchbyte)
            yield Ifne(index)
        elif isinstance(instruction, UnresolvedBranchIf2):
            branchbyte = pos + instruction.offset
            index = positions.index(branchbyte)
            yield BranchIf2(index, instruction.predicate)
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
