from dataclasses import dataclass


@dataclass
class Fieldref:
    TAG = 9
    class_index: int
    name_and_type_index: int
