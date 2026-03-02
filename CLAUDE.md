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

# Run tests across Python versions
uvx --with tox-uv tox

# Lint
uv run flake8

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
- Linting uses flake8 with flake8-bugbear; E501 (line length) is ignored.
