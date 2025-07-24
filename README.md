# QLang Quantum Programming Language

This repository contains a minimal implementation of **QLang**, a small quantum
computing language. The `qclang` directory provides a simple compiler that
translates `.ql` source files into OpenQASM 2.0, which can be executed by
quantum frameworks such as Qiskit.

## Features

- Classical variables with `let` assignments
- Quantum and classical bit declarations via `qubit` and `bit`
- Basic quantum gates: `h`, `x`, `cx`, `cz`, `swap`
- Measurement with `measure <qubit> -> <bit>`
- Classical `if` and `while` control flow (executed at compile time)

## Usage

Compile a QLang program to QASM:

```bash
python qclang/compiler.py examples/bell.ql examples/bell.qasm
```

The resulting `.qasm` file can be loaded into Qiskit or any other tool that
accepts OpenQASM 2.0.

## Example

The file `examples/bell.ql` creates a Bell state:

```text
qubit q0;
qubit q1;
bit c0;
bit c1;

h q0;
cx q0 q1;
measure q0 -> c0;
measure q1 -> c1;
```

Compiling it produces the following QASM:

```text
OPENQASM 2.0;
include "qelib1.inc";
qreg q0[1];
qreg q1[1];
creg c0[1];
creg c1[1];
h q0[0];
cx q0[0], q1[0];
measure q0[0] -> c0[0];
measure q1[0] -> c1[0];
```

This QASM can be executed using Qiskit to run on real or simulated quantum
hardware.

