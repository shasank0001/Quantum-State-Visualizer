export type GateMeta = {
  type: 'H' | 'X' | 'Y' | 'Z' | 'S' | 'T' | 'RX' | 'RY' | 'RZ' | 'CNOT' | 'CZ' | 'SWAP';
  label: string;
  name: string;
  description: string;
  qasm: string;
  twoQ?: boolean;
  learnUrl?: string;
  details?: string;
  matrix?: string; // rendered as monospace block when present
};

export const GATE_METADATA: GateMeta[] = [
  {
    type: 'H',
    label: 'H',
    name: 'Hadamard',
    description: 'Creates equal superposition of |0⟩ and |1⟩.',
    qasm: 'h q[i];',
    learnUrl: 'https://qiskit.org/textbook/ch-states/representing-qubit-states.html',
  details: 'Maps |0⟩→(|0⟩+|1⟩)/√2 and |1⟩→(|0⟩−|1⟩)/√2. Bloch: 180° around the X+Z axis.',
  matrix: '1/√2 · [[1, 1],[1, -1]]',
  },
  {
    type: 'X',
    label: 'X',
    name: 'Pauli-X (NOT)',
    description: 'Bit-flip: |0⟩ ↔ |1⟩.',
    qasm: 'x q[i];',
    learnUrl: 'https://en.wikipedia.org/wiki/Pauli_matrices',
  details: 'Bloch: 180° rotation about the X axis (π rad).',
  matrix: '[[0, 1],[1, 0]]',
  },
  {
    type: 'Z',
    label: 'Z',
    name: 'Pauli-Z',
    description: 'Phase flip: adds a phase of π to |1⟩.',
    qasm: 'z q[i];',
    learnUrl: 'https://en.wikipedia.org/wiki/Pauli_matrices',
  details: 'Bloch: 180° rotation about the Z axis (π rad).',
  matrix: '[[1, 0],[0, -1]]',
  },
  {
    type: 'S',
    label: 'S',
    name: 'Phase (S)',
    description: 'Applies a phase of π/2 to |1⟩.',
    qasm: 's q[i];',
  details: 'Square root of Z: S·S = Z.',
  matrix: '[[1, 0],[0, i]]',
  },
  {
    type: 'T',
    label: 'T',
    name: 'T Gate',
    description: 'Applies a phase of π/4 to |1⟩.',
    qasm: 't q[i];',
  details: 'T·T = S and T⁴ = Z.',
  matrix: '[[1, 0],[0, e^{iπ/4}]]',
  },
  {
    type: 'Y',
    label: 'Y',
    name: 'Pauli-Y',
    description: 'Bit+phase flip.',
    qasm: 'y q[i];',
    learnUrl: 'https://en.wikipedia.org/wiki/Pauli_matrices',
    details: 'Bloch: 180° rotation about the Y axis (π rad).',
    matrix: '[[0, -i],[i, 0]]',
  },
  {
    type: 'RX',
    label: 'RX',
    name: 'Rotation X (π/2)',
    description: 'Rotate around X by π/2 (90°).',
    qasm: 'rx(pi/2) q[i];',
    learnUrl: 'https://qiskit.org/documentation/stubs/qiskit.circuit.library.RXGate.html',
    details: 'Common quick rotation; adjust in code editor for custom angles.',
  },
  {
    type: 'RY',
    label: 'RY',
    name: 'Rotation Y (π/2)',
    description: 'Rotate around Y by π/2 (90°).',
    qasm: 'ry(pi/2) q[i];',
    learnUrl: 'https://qiskit.org/documentation/stubs/qiskit.circuit.library.RYGate.html',
    details: 'Common quick rotation; adjust in code editor for custom angles.',
  },
  {
    type: 'RZ',
    label: 'RZ',
    name: 'Rotation Z (π/2)',
    description: 'Rotate around Z by π/2 (90°).',
    qasm: 'rz(pi/2) q[i];',
    learnUrl: 'https://qiskit.org/documentation/stubs/qiskit.circuit.library.RZGate.html',
    details: 'Common quick rotation; adjust in code editor for custom angles.',
  },
  {
    type: 'CNOT',
    label: 'CNOT',
    name: 'Controlled-X (CNOT)',
    description: 'Flips the target qubit if the control is |1⟩.',
    qasm: 'cx q[control], q[target];',
    twoQ: true,
    learnUrl: 'https://qiskit.org/textbook/ch-gates/more-circuit-identities.html',
  details: 'Truth table: |00⟩→|00⟩, |01⟩→|01⟩, |10⟩→|11⟩, |11⟩→|10⟩. Key entangling gate.',
  },
  {
    type: 'CZ',
    label: 'CZ',
    name: 'Controlled-Z (CZ)',
    description: 'Applies Z to the target when control is |1⟩ (adds conditional phase).',
    qasm: 'cz q[control], q[target];',
    twoQ: true,
  details: 'Diagonal(1,1,1,−1). Equivalent to CNOT up to local Hadamards.',
  matrix: 'diag(1, 1, 1, -1)',
  },
  {
    type: 'SWAP',
    label: 'SWAP',
    name: 'SWAP',
    description: 'Swap the states of two qubits.',
    qasm: 'swap q[control], q[target];',
    twoQ: true,
    details: 'Decomposes into 3 CNOTs: CX(a,b); CX(b,a); CX(a,b).',
    matrix: '[[1,0,0,0],[0,0,1,0],[0,1,0,0],[0,0,0,1]]',
  },
];
