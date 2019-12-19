import logging
from dataclasses import dataclass
from typing import BinaryIO, Tuple

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ClassFile:
    """
    https://docs.oracle.com/javase/specs/jvms/se11/html/jvms-4.html#jvms-4.1
    """

    magic: int
    minor_version: int
    major_version: int
    constant_pool_count: int
    constant_pool: tuple


def parse_class_file(stream: BinaryIO) -> ClassFile:
    reader = ClassFileReader(stream)

    magic = reader.next_u4()
    logger.debug(f"Read the field 'magic': {magic}")

    minor_version = reader.next_u2()
    logger.debug(f"Read the field 'minor_version': {minor_version}")

    major_version = reader.next_u2()
    logger.debug(f"Read the field 'major_version': {major_version}")

    constant_pool_count = reader.next_u2()
    logger.debug(f"Read the field 'constant_pool_count': {constant_pool_count}")

    constant_pool = ConstantPoolReader(reader, constant_pool_count).read()

    return ClassFile(
        magic, minor_version, major_version, constant_pool_count, constant_pool
    )


class ClassFileReader:
    def __init__(self, stream: BinaryIO):
        self.stream = stream

    def next_u4(self) -> int:
        return int.from_bytes(self.stream.read(4), byteorder="big")

    def next_u2(self) -> int:
        return int.from_bytes(self.stream.read(2), byteorder="big")

    def next_u1(self) -> int:
        return int.from_bytes(self.stream.read(1), byteorder="big")

    def read(self, n: int) -> bytes:
        return self.stream.read(n)


class ConstantPoolReader:
    """
    https://docs.oracle.com/javase/specs/jvms/se11/html/jvms-4.html#jvms-4.4
    """

    def __init__(self, reader: ClassFileReader, constant_pool_count: int):
        self.reader = reader
        self.constant_pool_count = constant_pool_count

    def read(self) -> Tuple[dict, ...]:
        return tuple(self._next() for _ in range(self.constant_pool_count - 1))

    def _next(self) -> dict:
        tag = self.reader.next_u1()
        if tag == 1:
            length = self.reader.next_u2()
            bytes_ = self.reader.read(length)
            info = {"tag": tag, "length": length, "bytes": bytes_}
            logger.debug(f"Read a Utf8_info: {info}")
            return info

        elif tag == 7:
            info = {"tag": tag, "name_index": self._read_index()}
            logger.debug(f"Read a Class_info: {info}")
            return info

        elif tag == 8:
            string_index = self._read_index()
            info = {"tag": tag, "string_index": string_index}
            logger.debug(f"Read a String_info: {info}")
            return info

        elif tag == 9:
            class_index = self._read_index()
            name_and_type_index = self._read_index()
            info = {
                "tag": tag,
                "class_index": class_index,
                "name_and_type_index": name_and_type_index,
            }
            logger.debug(f"Read a Fieldref_info: {info}")
            return info

        elif tag == 10:
            class_index = self._read_index()
            name_and_type_index = self._read_index()

            info = {
                "tag": tag,
                "class_index": class_index,
                "name_and_type_index": name_and_type_index,
            }
            logger.debug(f"Read a Methodref_info: {info}")
            return info

        elif tag == 12:
            info = {
                "tag": tag,
                "name_index": self._read_index(),
                "descriptor_index": self._read_index(),
            }
            logger.debug(f"Read a NameAndType_info: {info}")

        else:
            raise NotImplementedError(tag)

    def _read_index(self):
        index = self.reader.next_u2()
        assert index in range(1, self.constant_pool_count)
        return index
