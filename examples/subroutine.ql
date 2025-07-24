def bell_state(a, b) {
    h a;
    cx a b;
}

qubit q0;
qubit q1;
bit c0;
bit c1;

bell_state(q0, q1);
measure q0 -> c0;
measure q1 -> c1;
