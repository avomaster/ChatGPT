qubit q0;
qubit q1;
bit c0;
bit c1;

h q0;
cx q0 q1;
measure q0 -> c0;
measure q1 -> c1;
