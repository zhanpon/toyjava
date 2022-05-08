import logging
from dataclasses import dataclass
from io import BytesIO
from itertools import repeat
from typing import BinaryIO

from toyjava.constants import ConstantPoolReader, String
from toyjava.instructions import parse_instructions, Getstatic, Ldc, Invokevirtual, Return, Istore1, Iload1, Istore2, \
    Iload2, Iinc, Goto, Push, Ifne, BranchIf2, InvokeStatic, Iload0, Ireturn, Arithmetic2

logger = logging.getLogger(__name__)


class VirtualMachine:
    def execute_main(self, cls):
        # Assume the number of local variables is not more than 10
        local_variables = list(repeat(None, 10))
        instructions = cls.main_instructions()
        execute(instructions, cls, local_variables)


def execute(instructions, cls, local_variables):
    constant_pool = cls.constant_pool
    pc = 0
    operand_stack = []
    while True:
        instruction = instructions[pc]
        if isinstance(instruction, Getstatic):
            operand_stack.append(constant_pool[instruction.index])
        elif isinstance(instruction, Ldc):
            c = constant_pool[instruction.index]
            # Assume it is a String constant
            assert isinstance(c, String)
            value = constant_pool[c.string_index]
            operand_stack.append(value)
        elif isinstance(instruction, Invokevirtual):
            # Assume the method only has one argument
            methodref = constant_pool[instruction.index]
            arg1 = operand_stack.pop()
            objectref = operand_stack.pop()

            field_class = constant_pool[constant_pool[objectref.class_index].name_index]
            field_name = constant_pool[constant_pool[objectref.name_and_type_index].name_index]
            method_name = constant_pool[constant_pool[methodref.name_and_type_index].name_index]

            if field_class == "java/lang/System" and field_name == "out" and method_name == "println":
                print(arg1)
            else:
                raise NotImplementedError("'invokevirtual' is not implemented except System.out.println")
        elif isinstance(instruction, InvokeStatic):
            # stub
            methodref = constant_pool[instruction.index]
            name_and_type = constant_pool[methodref.name_and_type_index]
            descriptor = constant_pool[name_and_type.descriptor_index]
            # https://docs.oracle.com/javase/specs/jvms/se7/html/jvms-4.html#jvms-4.3.3
            num_args = sum(1 for c in descriptor[1:descriptor.find(")")] if c in ["I", "L"])
            method_name = constant_pool[name_and_type.name_index]

            next_instructions = cls.find_instructions(method_name)

            args = operand_stack[-num_args:]
            for _ in range(num_args):
                operand_stack.pop()

            return_value = execute(next_instructions, cls, args)
            operand_stack.append(return_value)
        elif isinstance(instruction, Return):
            return
        elif isinstance(instruction, Ireturn):
            return operand_stack.pop()
        elif isinstance(instruction, Push):
            operand_stack.append(instruction.value)
        elif isinstance(instruction, Arithmetic2):
            value2 = operand_stack.pop()
            value1 = operand_stack.pop()
            operand_stack.append(instruction.function(value1, value2))
        elif isinstance(instruction, Istore1):
            i = operand_stack.pop()
            local_variables[1] = i
        elif isinstance(instruction, Istore2):
            i = operand_stack.pop()
            local_variables[2] = i
        elif isinstance(instruction, Iload0):
            i = local_variables[0]
            operand_stack.append(i)
        elif isinstance(instruction, Iload1):
            i = local_variables[1]
            operand_stack.append(i)
        elif isinstance(instruction, Iload2):
            i = local_variables[2]
            operand_stack.append(i)
        elif isinstance(instruction, Ifne):
            value = operand_stack.pop()
            if value != 0:
                pc = instruction.index
                continue
        elif isinstance(instruction, BranchIf2):
            v2 = operand_stack.pop()
            v1 = operand_stack.pop()
            if instruction.predicate(v1, v2):
                pc = instruction.index
                continue
        elif isinstance(instruction, Iinc):
            local_variables[instruction.index] += instruction.const
        elif isinstance(instruction, Goto):
            pc = instruction.index
            continue
        else:
            raise NotImplementedError(instruction)

        pc += 1


@dataclass(frozen=True)
class ClassFile:
    """
    https://docs.oracle.com/javase/specs/jvms/se13/html/jvms-4.html#jvms-4.1
    """

    magic: int
    constant_pool_count: int
    constant_pool: tuple
    methods: tuple

    def find_method(self, name):
        for m in self.methods:
            utf8 = self.constant_pool[m.name_index]
            if utf8 == name:
                return m

    def find_instructions(self, name):
        code = self.find_method(name).code
        return parse_instructions(code)

    def main_instructions(self):
        return self.find_instructions("main")


def parse_class_file(class_file: bytes) -> ClassFile:
    stream = BytesIO(class_file)
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
    constant_pool = ConstantPoolReader(reader, constant_pool_count).read()

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
        https://docs.oracle.com/javase/specs/jvms/se13/html/jvms-4.html#jvms-4.6
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
        # https://docs.oracle.com/javase/specs/jvms/se13/html/jvms-4.html#jvms-4.7.3
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
