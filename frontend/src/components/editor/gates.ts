export type GateMeta = {
  type: 'H' | 'X' | 'Z' | 'S' | 'T' | 'CNOT' | 'CZ';
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
];
