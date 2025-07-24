qubit q0;
qubit q1;
bit c0;
bit c1;

h q0;
measure q0 -> c0;
if c0 == 1 {
    x q1;
}
measure q1 -> c1;
