from constants import Fieldref
from instructions import parse_instructions, Getstatic, Ldc, Invokevirtual, Return


def test_parse_instructions():
    code = bytes.fromhex("b2 00 02 12 03 b6 00 04 b1")
    assert parse_instructions(code) == (
        Getstatic(2),
        Ldc(3),
        Invokevirtual(4),
        Return(),
    )


def test_get_static():
    field = Fieldref(2, 3)
    operand_stack = []
    constant_pool = (None, field)
    new_stack = Getstatic(1).execute(constant_pool, operand_stack)
    assert operand_stack == []
    assert new_stack == [field]
