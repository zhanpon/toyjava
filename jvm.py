from typing import BinaryIO


class ClassFileReader:
    def __init__(self, stream: BinaryIO):
        self.stream = stream

    def next_u4(self) -> int:
        return int.from_bytes(self.stream.read(4), byteorder="big")
