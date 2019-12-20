from instructions import parse_instructions, Getstatic, Ldc, Invokevirtual, Return


def test_parse_instructions():
    code = bytes.fromhex("b2 00 02 12 03 b6 00 04 b1")
    assert parse_instructions(code) == (
        Getstatic(2),
        Ldc(3),
        Invokevirtual(4),
        Return(),
    )
