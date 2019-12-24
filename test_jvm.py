import logging
from pathlib import Path

import pytest

from instructions import Getstatic, Ldc, Invokevirtual, Return
from jvm import ClassFileReader, parse_class_file, VirtualMachine


def test_class_file_reader():
    with Path("data/Hello.class").open("rb") as f:
        reader = ClassFileReader(f)
        assert reader.next_u4() == int("0xCAFEBABE", 0)


def test_parse(caplog):
    caplog.set_level(logging.DEBUG)

    with Path("data/Hello.class").open("rb") as f:
        result = parse_class_file(f)
        assert result.magic == int("0xCAFEBABE", 0)
        assert len(result.constant_pool) == result.constant_pool_count


def test_main_instructions():
    with Path("data/Hello.class").open("rb") as f:
        result = parse_class_file(f)
        assert result.main_instructions() == (
            Getstatic(2),
            Ldc(3),
            Invokevirtual(4),
            Return(),
        )


@pytest.mark.parametrize("class_name,lines", [
    ("Hello", ["Hello World!"]),
    ("Bonjour", ["Bonjour le monde !"]),
    ("HelloGoodbye", ["Hello Summer,", "Goodbye"]),
    ("PrintInt", ["-1", "0", "1", "2", "3", "4", "5"])
])
def test_stdout(capsys, class_name, lines):
    path = Path("data") / f"{class_name}.class"
    expected_output = "".join(line + "\n" for line in lines)

    with path.open("rb") as f:
        cls = parse_class_file(f)
        vm = VirtualMachine()
        vm.execute_main(cls)
        captured = capsys.readouterr()
        assert captured.out == expected_output
