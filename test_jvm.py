from pathlib import Path

from jvm import ClassFileReader


def test_class_file_reader():
    with Path("data/Hello.class").open("rb") as f:
        reader = ClassFileReader(f)
        assert reader.next_u4() == int("0xCAFEBABE", 0)
