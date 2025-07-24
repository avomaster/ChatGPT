import re
import sys
from typing import List, Dict, Any

# Simple AST node classes
class Statement:
    """Base AST node"""
    pass

class FunctionDef:
    def __init__(self, name: str, params: List[str], body: List[Statement]):
        self.name = name
        self.params = params
        self.body = body

class FunctionCall(Statement):
    def __init__(self, name: str, args: List[str]):
        self.name = name
        self.args = args

class QubitDecl(Statement):
    def __init__(self, name: str, size: int = 1):
        self.name = name
        self.size = size

class BitDecl(Statement):
    def __init__(self, name: str, size: int = 1):
        self.name = name
        self.size = size

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
    def __init__(self, cond: str, then: List[Statement], else_: List[Statement], runtime: bool = False):
        self.cond = cond
        self.then = then
        self.else_ = else_
        self.runtime = runtime

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
        if c in "{}->;(),[]":
            if token:
                tokens.append(token)
                token = ""
            if c == '-' and i + 1 < len(line) and line[i+1] == '>':
                tokens.append('->')
                i += 2
                continue
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
        self.funcs: Dict[str, FunctionDef] = {}

    def peek(self) -> List[str]:
        if self.i < len(self.tokens):
            return self.tokens[self.i]
        return []

    def next(self) -> List[str]:
        t = self.peek()
        self.i += 1
        return t

    def parse_statement(self) -> List[Statement]:
        line = self.peek()
        if not line:
            self.next()
            return []
        tok = line[0]
        if tok == 'qubit':
            size = 1
            name_index = 1
            if len(line) > 2 and line[1] == '[':
                size = int(line[2])
                name_index = 4
            name = line[name_index].rstrip(';')
            self.next()
            return [QubitDecl(name, size)]
        elif tok == 'bit':
            size = 1
            name_index = 1
            if len(line) > 2 and line[1] == '[':
                size = int(line[2])
                name_index = 4
            name = line[name_index].rstrip(';')
            self.next()
            return [BitDecl(name, size)]
        elif tok == 'let':
            name = line[1]
            expr_tokens = line[3:]
            if expr_tokens and expr_tokens[-1] == ';':
                expr_tokens = expr_tokens[:-1]
            expr = ' '.join(expr_tokens)
            self.next()
            return [LetStmt(name, expr)]
        elif tok in {'h', 'x', 'cx', 'cz', 'swap', 'rx', 'ry', 'rz', 's', 'sdg', 't', 'tdg', 'ccx', 'cswap'}:
            args = []
            j = 1
            while j < len(line):
                t = line[j]
                if t in {',', ';'}:
                    j += 1
                    continue
                if j + 3 < len(line) and line[j+1] == '[':
                    args.append(f"{t}[{line[j+2]}]")
                    j += 4
                else:
                    args.append(t)
                    j += 1
            self.next()
            return [GateStmt(tok, args)]
        elif tok == 'measure':
            arrow = line.index('->')
            qubit = ''.join(line[1:arrow])
            bit_tokens = [t for t in line[arrow+1:] if t != ';']
            bit = ''.join(bit_tokens)
            self.next()
            return [MeasureStmt(qubit, bit)]
        elif tok == 'def':
            name = line[1]
            assert line[2] == '('
            params = []
            j = 3
            while line[j] != ')':
                if line[j] != ',':
                    params.append(line[j])
                j += 1
            self.next()  # consume def line
            body = self.parse_block()
            self.funcs[name] = FunctionDef(name, params, body)
            return []
        elif tok == 'if':
            cond = ' '.join(line[1:])
            assert cond.endswith('{'), 'expected {'
            cond = cond[:-1].strip()
            self.next()
            then = self.parse_block()
            else_block = []
            if self.i < len(self.tokens) and self.peek() and self.peek()[0] == 'else':
                self.next()
                else_block = self.parse_block()
            runtime = '==' in cond or '!=' in cond
            return [IfStmt(cond, then, else_block, runtime)]
        elif tok == 'while':
            cond = ' '.join(line[1:])
            assert cond.endswith('{'), 'expected {'
            cond = cond[:-1].strip()
            self.next()
            body = self.parse_block()
            return [WhileStmt(cond, body)]
        elif re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', tok) and '(' in line:
            name = tok
            args = []
            j = 1
            while j < len(line) and line[j] != ')':
                if line[j] not in {',', '('}:
                    args.append(line[j])
                j += 1
            self.next()
            return [FunctionCall(name, args)]
        else:
            self.next()
            return []

    def parse_program(self) -> List[Statement]:
        stmts = []
        while self.i < len(self.tokens):
            stmts.extend(self.parse_statement())
        return stmts

    def parse_block(self) -> List[Statement]:
        stmts = []
        while self.i < len(self.tokens):
            line = self.peek()
            if line and line[0] == '}':
                self.next()
                break
            stmts.extend(self.parse_statement())
        return stmts

# Interpreter to build QASM

class Compiler:
    def __init__(self, funcs: Dict[str, FunctionDef]):
        self.qasm = ["OPENQASM 2.0;", 'include "qelib1.inc";']
        self.qubits: Dict[str, int] = {}
        self.bits: Dict[str, int] = {}
        self.vars: Dict[str, Any] = {}
        self.funcs = funcs

    def add_qubit(self, name: str, size: int = 1):
        if name not in self.qubits:
            self.qubits[name] = size
            self.qasm.append(f"qreg {name}[{size}];")

    def add_bit(self, name: str, size: int = 1):
        if name not in self.bits:
            self.bits[name] = size
            self.qasm.append(f"creg {name}[{size}];")

    def format_qubit(self, name: str) -> str:
        return name if '[' in name else f"{name}[0]"

    def format_bit(self, name: str) -> str:
        return name if '[' in name else f"{name}[0]"

    def gate(self, gate: str, args: List[str], cond: str | None = None):
        if gate in {'rx', 'ry', 'rz'}:
            qubit = self.format_qubit(args[0])
            angle = args[1]
            line = f"{gate}({angle}) {qubit};"
        else:
            args_fmt = ', '.join(self.format_qubit(a) for a in args)
            line = f"{gate} {args_fmt};"
        if cond:
            self.qasm.append(f"if({cond}) {line}")
        else:
            self.qasm.append(line)

    def measure(self, qubit: str, bit: str, cond: str | None = None):
        line = f"measure {self.format_qubit(qubit)} -> {self.format_bit(bit)};"
        if cond:
            self.qasm.append(f"if({cond}) {line}")
        else:
            self.qasm.append(line)

    def eval_expr(self, expr: str) -> Any:
        return eval(expr, {}, self.vars)

    def compile_stmt(self, stmt: Statement, mapping: Dict[str, str] | None = None, cond: str | None = None):
        mapping = mapping or {}
        if isinstance(stmt, QubitDecl):
            name = mapping.get(stmt.name, stmt.name)
            self.add_qubit(name, stmt.size)
        elif isinstance(stmt, BitDecl):
            name = mapping.get(stmt.name, stmt.name)
            self.add_bit(name, stmt.size)
        elif isinstance(stmt, LetStmt):
            self.vars[stmt.name] = self.eval_expr(stmt.expr)
        elif isinstance(stmt, GateStmt):
            args = [mapping.get(a, a) for a in stmt.args]
            self.gate(stmt.gate, args, cond)
        elif isinstance(stmt, MeasureStmt):
            qu = mapping.get(stmt.qubit, stmt.qubit)
            bt = mapping.get(stmt.bit, stmt.bit)
            self.measure(qu, bt, cond)
        elif isinstance(stmt, FunctionCall):
            args = [mapping.get(a, a) for a in stmt.args]
            self.compile_function(stmt.name, args, cond)
        elif isinstance(stmt, IfStmt):
            if stmt.runtime:
                cond_str = stmt.cond.replace(' ', '')
                for s in stmt.then:
                    self.compile_stmt(s, mapping, cond_str)
                if stmt.else_:
                    neg = cond_str.replace('==1', '==0').replace('==0', '==1')
                    for s in stmt.else_:
                        self.compile_stmt(s, mapping, neg)
            else:
                cond_val = self.eval_expr(stmt.cond)
                target = stmt.then if cond_val else stmt.else_
                for s in target:
                    self.compile_stmt(s, mapping)
        elif isinstance(stmt, WhileStmt):
            while self.eval_expr(stmt.cond):
                for s in stmt.body:
                    self.compile_stmt(s, mapping)
        else:
            raise ValueError(f"Unknown stmt {stmt}")

    def compile(self, program: List[Statement]):
        for stmt in program:
            self.compile_stmt(stmt)

    def compile_function(self, name: str, args: List[str], cond: str | None = None):
        if name not in self.funcs:
            raise ValueError(f"Undefined function {name}")
        func = self.funcs[name]
        if len(args) != len(func.params):
            raise ValueError(f"Argument mismatch in call to {name}")
        mapping = dict(zip(func.params, args))
        for st in func.body:
            self.compile_stmt(st, mapping, cond)

    def to_qasm(self) -> str:
        return "\n".join(self.qasm) + "\n"


def compile_file(path: str) -> str:
    with open(path) as f:
        code = f.read()
    code = remove_comments(code)
    lines = [tokenize(line) for line in code.splitlines() if line.strip()]
    parser = Parser(lines)
    program = parser.parse_program()
    comp = Compiler(parser.funcs)
    comp.compile(program)
    return comp.to_qasm()

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("usage: python compiler.py <input.ql> <output.qasm>")
        sys.exit(1)
    qasm = compile_file(sys.argv[1])
    with open(sys.argv[2], 'w') as f:
        f.write(qasm)
