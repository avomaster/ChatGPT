import re
import sys
from typing import List, Dict, Any

# Simple AST node classes
class Statement:
    pass

class QubitDecl(Statement):
    def __init__(self, name: str):
        self.name = name

class BitDecl(Statement):
    def __init__(self, name: str):
        self.name = name

class LetStmt(Statement):
    def __init__(self, name: str, expr: str):
        self.name = name
        self.expr = expr

class GateStmt(Statement):
    def __init__(self, gate: str, args: List[str]):
        self.gate = gate
        self.args = args

class MeasureStmt(Statement):
    def __init__(self, qubit: str, bit: str):
        self.qubit = qubit
        self.bit = bit

class IfStmt(Statement):
    def __init__(self, cond: str, then: List[Statement], else_: List[Statement]):
        self.cond = cond
        self.then = then
        self.else_ = else_

class WhileStmt(Statement):
    def __init__(self, cond: str, body: List[Statement]):
        self.cond = cond
        self.body = body

# Parser functions

def remove_comments(code: str) -> str:
    lines = []
    for line in code.splitlines():
        idx = line.find("//")
        if idx != -1:
            line = line[:idx]
        lines.append(line)
    return "\n".join(lines)

def tokenize(line: str) -> List[str]:
    tokens = []
    token = ""
    i = 0
    while i < len(line):
        c = line[i]
        if c.isspace():
            if token:
                tokens.append(token)
                token = ""
            i += 1
            continue
        if c in "{}->;":
            if token:
                tokens.append(token)
                token = ""
            if c == '-' and i + 1 < len(line) and line[i+1] == '>':
                tokens.append('->')
                i += 2
                continue
            if c != ';':
                tokens.append(c)
            i += 1
            continue
        token += c
        i += 1
    if token:
        tokens.append(token)
    return tokens

class Parser:
    def __init__(self, tokens: List[List[str]]):
        self.tokens = tokens
        self.i = 0

    def peek(self) -> List[str]:
        if self.i < len(self.tokens):
            return self.tokens[self.i]
        return []

    def next(self) -> List[str]:
        t = self.peek()
        self.i += 1
        return t

    def parse_program(self) -> List[Statement]:
        stmts = []
        while self.i < len(self.tokens):
            line = self.peek()
            if not line:
                self.next()
                continue
            tok = line[0]
            if tok == 'qubit':
                stmts.append(QubitDecl(line[1].rstrip(';')))
                self.next()
            elif tok == 'bit':
                stmts.append(BitDecl(line[1].rstrip(';')))
                self.next()
            elif tok == 'let':
                name = line[1]
                expr_tokens = line[3:]
                if expr_tokens and expr_tokens[-1] == ';':
                    expr_tokens = expr_tokens[:-1]
                expr = ' '.join(expr_tokens)
                stmts.append(LetStmt(name, expr))
                self.next()
            elif tok in {'h', 'x', 'cx', 'cz', 'swap'}:
                args = line[1:]
                if args and args[-1] == ';':
                    args = args[:-1]
                stmts.append(GateStmt(tok, args))
                self.next()
            elif tok == 'measure':
                arrow = line.index('->')
                qubit = line[1]
                bit = line[arrow + 1]
                stmts.append(MeasureStmt(qubit, bit))
                self.next()
            elif tok == 'if':
                cond = ' '.join(line[1:])
                assert cond.endswith('{'), 'expected {'
                cond = cond[:-1].strip()
                self.next()
                then = self.parse_block()
                else_block = []
                if self.i < len(self.tokens) and self.peek() and self.peek()[0] == 'else':
                    self.next()  # consume else {
                    else_block = self.parse_block()
                stmts.append(IfStmt(cond, then, else_block))
            elif tok == 'while':
                cond = ' '.join(line[1:])
                assert cond.endswith('{'), 'expected {'
                cond = cond[:-1].strip()
                self.next()
                body = self.parse_block()
                stmts.append(WhileStmt(cond, body))
            else:
                self.next()
        return stmts

    def parse_block(self) -> List[Statement]:
        stmts = []
        while self.i < len(self.tokens):
            line = self.peek()
            if line and line[0] == '}':
                self.next()
                break
            stmt = self.parse_program()
            stmts.extend(stmt)
        return stmts

# Interpreter to build QASM

class Compiler:
    def __init__(self):
        self.qasm = ["OPENQASM 2.0;", 'include "qelib1.inc";']
        self.qubits: Dict[str, int] = {}
        self.bits: Dict[str, int] = {}
        self.vars: Dict[str, Any] = {}

    def add_qubit(self, name: str):
        if name not in self.qubits:
            self.qubits[name] = 0
            self.qasm.append(f"qreg {name}[1];")

    def add_bit(self, name: str):
        if name not in self.bits:
            self.bits[name] = 0
            self.qasm.append(f"creg {name}[1];")

    def gate(self, gate: str, args: List[str]):
        args_fmt = ', '.join(f"{a}[0]" for a in args)
        self.qasm.append(f"{gate} {args_fmt};")

    def measure(self, qubit: str, bit: str):
        self.qasm.append(f"measure {qubit}[0] -> {bit}[0];")

    def eval_expr(self, expr: str) -> Any:
        return eval(expr, {}, self.vars)

    def compile_stmt(self, stmt: Statement):
        if isinstance(stmt, QubitDecl):
            self.add_qubit(stmt.name)
        elif isinstance(stmt, BitDecl):
            self.add_bit(stmt.name)
        elif isinstance(stmt, LetStmt):
            self.vars[stmt.name] = self.eval_expr(stmt.expr)
        elif isinstance(stmt, GateStmt):
            self.gate(stmt.gate, stmt.args)
        elif isinstance(stmt, MeasureStmt):
            self.measure(stmt.qubit, stmt.bit)
        elif isinstance(stmt, IfStmt):
            cond = self.eval_expr(stmt.cond)
            if cond:
                for s in stmt.then:
                    self.compile_stmt(s)
            else:
                for s in stmt.else_:
                    self.compile_stmt(s)
        elif isinstance(stmt, WhileStmt):
            while self.eval_expr(stmt.cond):
                for s in stmt.body:
                    self.compile_stmt(s)
        else:
            raise ValueError(f"Unknown stmt {stmt}")

    def compile(self, program: List[Statement]):
        for stmt in program:
            self.compile_stmt(stmt)

    def to_qasm(self) -> str:
        return "\n".join(self.qasm) + "\n"


def compile_file(path: str) -> str:
    with open(path) as f:
        code = f.read()
    code = remove_comments(code)
    lines = [tokenize(line) for line in code.splitlines() if line.strip()]
    parser = Parser(lines)
    program = parser.parse_program()
    comp = Compiler()
    comp.compile(program)
    return comp.to_qasm()

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("usage: python compiler.py <input.ql> <output.qasm>")
        sys.exit(1)
    qasm = compile_file(sys.argv[1])
    with open(sys.argv[2], 'w') as f:
        f.write(qasm)
