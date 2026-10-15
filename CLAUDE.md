# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

`toyjava` is a toy JVM (Java Virtual Machine) interpreter written in Python. It parses compiled Java `.class` files and executes JVM bytecode instructions using a stack-based virtual machine.

## Commands

```bash
# Install dependencies and package
uv sync --group dev

# Run tests
uv run pytest

# Run a single test
uv run pytest tests/test_jvm.py::test_hello

# Run lint and tests across Python versions
uvx --with tox-uv tox

# Run all pre-commit hooks (including Ruff) through tox
uvx --with tox-uv tox -e lint

# Run the interpreter
uv run bin/toyjava data/Hello.class
```

## Architecture

The execution pipeline is: `.class` file → `ClassFile` (parsed binary) → bytecode instructions → `VirtualMachine` (stack-based execution).

**`src/toyjava/constants.py`** — Reads the constant pool from a `.class` file. Handles UTF8, Class, String, Fieldref, Methodref, and NameAndType constant types.

**`src/toyjava/instructions.py`** — Defines bytecode instruction parsing and branch offset resolution. Each instruction is a dataclass with an opcode and optional operands.

**`src/toyjava/jvm.py`** — Core engine:
- `ClassFile`: dataclass produced by parsing a `.class` file header, constant pool, methods, and attributes.
- `VirtualMachine`: executes instructions using an operand stack and a fixed-size (10-slot) local variable array.
- Only `System.out.println` is currently wired as an external call via `invokevirtual`.

**`data/`** — Compiled `.class` files and their corresponding `.java` sources used as test fixtures. The test suite (`tests/test_jvm.py`) runs the VM against these files and checks stdout.

## Constraints

- Python >= 3.10 required (uses `match`/`case` and other modern syntax).
- `fields_count != 0` raises `NotImplementedError` — field support is not implemented.
- Local variable arrays are hardcoded to 10 slots.
- The tox lint environment runs all pre-commit hooks, including Ruff with pycodestyle, Pyflakes, bugbear, and Python 3.10 upgrade rules; E501 (line length) is ignored. Tests and `bin/toyjava` are included.
