import logging
from dataclasses import dataclass
from typing import BinaryIO, Tuple

from instructions import parse_instructions, Getstatic, Ldc, Invokevirtual, Return

logger = logging.getLogger(__name__)


class VirtualMachine:
    def __init__(self):
        self.operand_stack = []

    def execute_main(self, cls):
        constant_pool = cls.constant_pool
        instructions = cls.main_instructions()
        for instruction in instructions:
            if isinstance(instruction, Getstatic):
                self.operand_stack.append(constant_pool[instruction.index])
            elif isinstance(instruction, Ldc):
                self.operand_stack.append(constant_pool[instruction.index])
            elif isinstance(instruction, Invokevirtual):
                # Assume the method only has one argument
                methodref = constant_pool[instruction.index]
                arg1 = self.operand_stack.pop()
                objectref = self.operand_stack.pop()

                field_class = constant_pool[constant_pool[objectref["class_index"]]["name_index"]]["bytes"].decode()
                field_name = constant_pool[constant_pool[objectref["name_and_type_index"]]["name_index"]]["bytes"].decode()
                method_name = constant_pool[constant_pool[methodref["name_and_type_index"]]["name_index"]]["bytes"].decode()

                if field_class != "java/lang/System" or field_name != "out" or method_name != "println":
                    raise NotImplementedError

                arg1_str = constant_pool[arg1["string_index"]]["bytes"].decode()
                print(arg1_str)
            elif isinstance(instruction, Return):
                return
            else:
                raise NotImplementedError(instruction)


@dataclass(frozen=True)
class ClassFile:
    """
    https://docs.oracle.com/javase/specs/jvms/se11/html/jvms-4.html#jvms-4.1
    """

    magic: int
    constant_pool_count: int
    constant_pool: tuple
    methods: tuple

    def _main_method(self):
        for m in self.methods:
            utf8 = self.constant_pool[m.name_index]
            if utf8["bytes"].decode() == "main":
                return m

    def main_instructions(self):
        main_code = self._main_method().code
        return parse_instructions(main_code)


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

    # The index starts from 1
    constant_pool = (None,) + ConstantPoolReader(reader, constant_pool_count).read()

    access_flags = reader.next_u2()
    logger.debug(f"Read the field 'access_flags': {access_flags}")

    this_class = reader.next_u2()
    logger.debug(f"Read the field 'this_class': {this_class}")

    super_class = reader.next_u2()
    logger.debug(f"Read the field 'super_class': {super_class}")

    interfaces_count = reader.next_u2()
    logger.debug(f"Read the field 'interfaces_count: {interfaces_count}")

    for _ in range(interfaces_count):
        interface = reader.next_u2()
        logger.debug(f"Read an interface {interface}")

    fields_count = reader.next_u2()
    logger.debug(f"Read the field 'fields_count': {fields_count}")

    if fields_count != 0:
        raise NotImplementedError

    methods_count = reader.next_u2()
    logger.debug(f"Read the field 'methods_count': {methods_count}")

    methods = MethodsReader(reader, methods_count).read()

    attributes_count = reader.next_u2()
    logger.debug(f"Read the field 'attributes_count': {attributes_count}")

    for _ in range(attributes_count):
        reader.next_u2()
        attributes_count = reader.next_u4()
        for _ in range(attributes_count):
            reader.next_u1()

    assert reader.read(1) == b""

    return ClassFile(magic, constant_pool_count, constant_pool, methods)


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
            return info
        else:
            raise NotImplementedError(tag)

    def _read_index(self):
        index = self.reader.next_u2()
        assert index in range(1, self.constant_pool_count)
        return index


@dataclass
class Method:
    name_index: int
    code: bytes


class MethodsReader:
    def __init__(self, reader: ClassFileReader, methods_count: int):
        self.reader = reader
        self.methods_count = methods_count

    def _next(self):
        """
        https://docs.oracle.com/javase/specs/jvms/se11/html/jvms-4.html#jvms-4.6
        """

        access_flags = self.reader.next_u2()
        logger.debug(f"Read the field 'access_flags': {access_flags}")

        name_index = self.reader.next_u2()
        logger.debug(f"Read the field 'name_index': {name_index}")

        descriptor_index = self.reader.next_u2()
        logger.debug(f"Read the field 'descriptor_index': {descriptor_index}")

        attributes_count = self.reader.next_u2()
        logger.debug(f"Read the field 'attributes_count': {attributes_count}")

        # Assume it is CodeAttribute:
        # https://docs.oracle.com/javase/specs/jvms/se11/html/jvms-4.html#jvms-4.7.3
        assert attributes_count == 1

        attribute_name_index = self.reader.next_u2()
        logger.debug(f"Read the field 'attribute_name_index': {attribute_name_index}")
        attribute_length = self.reader.next_u4()
        logger.debug(f"Read the field 'attribute_length': {attribute_length}")

        # info = self.reader.read(attribute_length)
        # logger.debug(f"Read the field 'info' {info.hex()}")

        max_stack = self.reader.next_u2()
        logger.debug(f"Read the field 'max_stack': {max_stack}")

        max_locals = self.reader.next_u2()

        code_length = self.reader.next_u4()
        logger.debug(f"Read the field 'code_length': {code_length}")

        code = self.reader.read(code_length)
        logger.debug(f"Read the field 'code': {code}")

        exception_table_length = self.reader.next_u2()
        logger.debug(
            f"Read the field 'exception_table_length': {exception_table_length}"
        )
        for _ in range(exception_table_length):
            self.reader.read(8)

        attributes_count = self.reader.next_u2()
        logger.debug(f"Read the field 'attributes_count': {attributes_count}")
        for _ in range(attributes_count):
            attribute_name_index2 = self.reader.next_u2()
            attribute_length2 = self.reader.next_u4()
            self.reader.read(attribute_length2)

        return Method(name_index, code)

    def read(self):
        return tuple(self._next() for _ in range(self.methods_count))
