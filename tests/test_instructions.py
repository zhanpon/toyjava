from toyjava.instructions import *


def test_parse_instructions():
    code = bytes.fromhex("b2 00 02 12 03 b6 00 04 b1")
    assert parse_instructions(code) == (
        Getstatic(2),
        Ldc(3),
        Invokevirtual(4),
        Return(),
    )


def test_parse_instructions2():
    code = bytes.fromhex("03 3c 1b 08 a20010 b20007 1b b6000d 840101 a7fff1 b1")
    assert parse_instructions(code) == (
        Push(0),
        Istore1(),
        Iload1(),
        Push(5),
        BranchIf2(index=10, predicate=op.ge),
        Getstatic(index=7),
        Iload1(),
        Invokevirtual(index=13),
        Iinc(index=1, const=1),
        Goto(index=2),
        Return(),
    )


def test_instruction_reader():
    code = bytes.fromhex("03 3c 1b 08 a20010 b20007 1b b6000d 840101 a7fff1 b1")
    raw_instructions, positions = InstructionReader(BytesIO(code)).read()
    assert raw_instructions == (
        Push(0),
        Istore1(),
        Iload1(),
        Push(5),
        UnresolvedBranchIf2(offset=16, predicate=op.ge),
        Getstatic(index=7),
        Iload1(),
        Invokevirtual(index=13),
        Iinc(index=1, const=1),
        RawGoto(branchbyte=-15),
        Return(),
    )
    assert positions == [0, 1, 2, 3, 4, 7, 10, 11, 14, 17, 20]
