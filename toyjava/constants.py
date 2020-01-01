import logging
from dataclasses import dataclass
from typing import Tuple

logger = logging.getLogger(__name__)


class ConstantPool:
    def __init__(self, constants):
        self._constants = constants

    def __getitem__(self, item):
        return self._constants[item - 1]

    def __len__(self):
        return len(self._constants)


@dataclass
class Fieldref:
    TAG = 9
    class_index: int
    name_and_type_index: int


class ConstantPoolReader:
    """
    https://docs.oracle.com/javase/specs/jvms/se13/html/jvms-4.html#jvms-4.4
    """

    def __init__(self, reader, constant_pool_count: int):
        self.reader = reader
        self.constant_pool_count = constant_pool_count

    def read(self) -> Tuple[dict, ...]:
        return ConstantPool(tuple(self._next() for _ in range(self.constant_pool_count - 1)))

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
            return info
        else:
            raise NotImplementedError(tag)

    def _read_index(self):
        index = self.reader.next_u2()
        assert index in range(1, self.constant_pool_count)
        return index