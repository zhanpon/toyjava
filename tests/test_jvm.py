import logging
from pathlib import Path

import pytest

from toyjava.jvm import ClassFileReader, parse_class_file, VirtualMachine


def test_class_file_reader():
    with Path("data/Hello.class").open("rb") as f:
        reader = ClassFileReader(f)
        assert reader.next_u4() == int("0xCAFEBABE", 0)


@pytest.mark.parametrize("class_name,lines", [
    ("Hello", ["Hello World!"]),
    ("Bonjour", ["Bonjour le monde !"]),
    ("HelloGoodbye", ["Hello Summer,", "Goodbye"]),
    ("PrintInt", ["-1", "0", "1", "2", "3", "4", "5"]),
    ("LocalVariables", ["1", "2"]),
    ("CountUp", ["0", "1", "2", "3", "4"]),
    ("FizzBuzz", ["1", "2", "Fizz", "4", "Buzz", "Fizz", "7", "8", "Fizz", "Buzz",
                  "11", "Fizz", "13", "14", "FizzBuzz", "16", "17", "Fizz", "19", "Buzz"]),
    ("StaticMethod", ["3"]),
    ("Factorial", ["3628800"])
])
def test_stdout(capsys, class_name, lines):
    path = Path("data") / f"{class_name}.class"
    expected_output = "".join(line + "\n" for line in lines)

    cls = parse_class_file(path.read_bytes())
    vm = VirtualMachine()
    vm.execute_main(cls)
    captured = capsys.readouterr()
    assert captured.out == expected_output
