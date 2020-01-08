import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

TAG_UTF8 = 1
TAG_CLASS = 7
TAG_STRING = 8
TAG_FIELDREF = 9
TAG_METHODREF = 10
TAG_NAME_AND_TYPE = 12


class ConstantPool:
    def __init__(self, constants):
        self._constants = constants

    def __getitem__(self, item):
        return self._constants[item - 1]

    def __len__(self):
        return len(self._constants)


@dataclass
class String:
    string_index: int


@dataclass
class Class:
    name_index: int


@dataclass
class Fieldref:
    class_index: int
    name_and_type_index: int


@dataclass
class Methodref:
    class_index: int
    name_and_type_index: int


@dataclass
class NameAndType:
    name_index: int
    descriptor_index: int


class ConstantPoolReader:
    """
    https://docs.oracle.com/javase/specs/jvms/se13/html/jvms-4.html#jvms-4.4
    """

    def __init__(self, reader, constant_pool_count: int):
        self.reader = reader
        self.constant_pool_count = constant_pool_count

    def read(self) -> ConstantPool:
        return ConstantPool(tuple(self._next() for _ in range(self.constant_pool_count - 1)))

    def _next(self):
        tag = self.reader.next_u1()
        if tag == TAG_UTF8:
            length = self.reader.next_u2()
            bytes_ = self.reader.read(length)
            info = {"tag": tag, "length": length, "bytes": bytes_}
            logger.debug(f"Read a Utf8_info: {info}")
            return bytes_.decode()

        elif tag == TAG_CLASS:
            info = Class(
                name_index=self._read_index()
            )
            logger.debug(f"Read a Class_info: {info}")
            return info

        elif tag == TAG_STRING:
            info = String(string_index=self._read_index())
            logger.debug(f"Read a String_info: {info}")
            return info

        elif tag == TAG_FIELDREF:
            info = Fieldref(
                class_index=self._read_index(),
                name_and_type_index=self._read_index()
            )
            logger.debug(f"Read a Fieldref_info: {info}")
            return info

        elif tag == TAG_METHODREF:
            info = Methodref(
                class_index=self._read_index(),
                name_and_type_index=self._read_index()
            )
            logger.debug(f"Read a Methodref_info: {info}")
            return info

        elif tag == TAG_NAME_AND_TYPE:
            info = NameAndType(
                name_index=self._read_index(),
                descriptor_index=self._read_index()
            )
            logger.debug(f"Read a NameAndType_info: {info}")
            return info
        else:
            raise NotImplementedError(tag)

    def _read_index(self):
        index = self.reader.next_u2()
        assert index in range(1, self.constant_pool_count)
        return index
