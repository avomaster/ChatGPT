qubit q0;
qubit q1;
qubit q2;

rx q0, 1.57;
ry q1, 0.78;
rz q2, 3.14;

s q0;
sdg q1;
t q2;
tdg q0;

ccx q0 q1 q2;
cswap q0 q1 q2;
