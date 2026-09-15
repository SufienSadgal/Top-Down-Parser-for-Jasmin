# Jasmin Language Top-Down Parser

A custom, light-weight Lexer and Top-Down Recursive Descent Parser written in Python for the **[Jasmin programming language](https://github.com/jasmin-lang/jasmin)**. 

This tool tokenizes Jasmin source code files and builds a structured, human-readable Abstract Syntax Tree (AST) to facilitate static analysis, code visualization, or down-stream compilation passes.

---

## 📌 Project Overview

Jasmin is a language for high-assurance and high-performance cryptography, blending high-level structured control flow with low-level assembly-like control over memory, registers, and instructions.

This repository implements:
1. **Lexical Analysis (`lexer.py`)**: A regular expression-based tokenizer that processes source code strings into a stream of typed tokens with full line/column location tracking for precise error reporting.
2. **Syntactic Analysis (`parser_topdown.py`)**: A top-down recursive descent parser that validates token sequences against the Jasmin grammar rules and constructs a hierarchical AST.
3. **AST Tree Visualization**: Built-in tree printing capabilities to visually inspect the syntax tree structure of any parsed module.

---

## ✨ Features & Grammar Support

The parser supports a comprehensive subset of the Jasmin language syntax, including low-level hardware abstractions:

* **Control Flow Constructs:** `if/else` conditionals, `while`, `do-while`, and `for` loops (with `to`/`downto` directions and step expressions), as well as `break` and `continue` statements.
* **Function Definitions:** Inline (`inline`) and exported (`export`) functions, complete with parameters, return signatures, storage classes, and function annotations (`#[inline]`).
* **Memory & Variable Operations:**
  * Explicit storage qualifiers (`reg`, `stack`, `inline`, `global`).
  * Explicit memory access with type annotations (e.g., `[:u8 in + 0]`).
  * Array indexing and slice extractions (e.g., `range`, `+:` width slices).
* **Hardware-Specific Features:**
  * Native support for CPU flags (`cf`, `zf`, `sf`, `of`, `pf`) and wildcards (`?`).
  * Intrinsics and SIMD vector operations (e.g., `#VPSLLV_4u32`, `pack`, `unpack`).
* **Expressions & Operators:** Full operator precedence support for binary arithmetic, bitwise shifts (`<<r`, `>>r`), logical operations, unary operators, ternary expressions (`? :`), type casting, and literals (hexadecimal, decimal, strings, booleans).

---

## 🛠️ Architecture

### Abstract Syntax Tree (AST) Structure
The parser transforms tokens into strongly-typed AST nodes derived from the base `ASTNode` class:

* `ProgramNode` / `FunctionNode`: High-level entry points and functional units.
* `BlockNode` / `AssignNode` / `VarDeclNode`: Statement execution blocks and variable state updates.
* `IfNode` / `ForNode` / `WhileNode`: Logical control flow branches.
* `MemAccessNode` / `SliceAccessNode` / `FlagNode`: Hardware and memory manipulation abstractions.
* `BinOpNode` / `UnaryOpNode` / `TernaryNode`: Expression evaluation trees.

---

## 🚀 Usage

### Prerequisites
* Python 3.8+

### Running the Parser

You can run the parser directly on the included sample code snippets to generate and display the AST:

```bash
python parser_topdown.py
Integration Example
Python
from lexer import Lexer
from parser_topdown import Parser

jasmin_code = """
fn add_one(reg u32 x) -> reg u32 {
    reg u32 res;
    res = x + 1;
    return res;
}
"""

# 1. Tokenize input source
lexer = Lexer(jasmin_code)
tokens = lexer.tokenize()

# 2. Parse tokens into AST
parser = Parser(tokens)
ast_root = parser.parse_module()

# 3. Print AST representation
ast_root.print_tree()
Sample AST Output
Plaintext
Parsing completato con successo!

└── Program
  └── Function: add_one
    ├── Args
      └── reg u32 x
    ├── Returns: (reg u32)
    └── Block
      └── Decl: reg u32 [res]
      └── Assign (=)
        ├── Targets
          └── Var: res
        └── Value
          └── BinOp: +
            └── Var: x
            └── INT: 1
      └── Return
        └── Var: res
