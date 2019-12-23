import logging
from pathlib import Path

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


def test_execute(capsys):
    with Path("data/Hello.class").open("rb") as f:
        cls = parse_class_file(f)
        vm = VirtualMachine()
        vm.execute_main(cls)
        captured = capsys.readouterr()
        assert captured.out == "Hello World!\n"


def test_execute2(capsys):
    with Path("data/Bonjour.class").open("rb") as f:
        cls = parse_class_file(f)
        vm = VirtualMachine()
        vm.execute_main(cls)
        captured = capsys.readouterr()
        assert captured.out == "Bonjour le monde !\n"


def test_execute3(capsys):
    with Path("data/HelloGoodbye.class").open("rb") as f:
        cls = parse_class_file(f)
        vm = VirtualMachine()
        vm.execute_main(cls)
        captured = capsys.readouterr()
        assert captured.out == "Hello Summer,\nGoodbye\n"


def test_print_int(capsys):
    with Path("data/PrintInt.class").open("rb") as f:
        cls = parse_class_file(f)
        vm = VirtualMachine()
        vm.execute_main(cls)
        captured = capsys.readouterr()
        assert captured.out == "2\n"
