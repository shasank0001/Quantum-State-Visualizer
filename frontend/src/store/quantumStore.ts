import { create } from 'zustand';
import { quantumAPI, type SimulationRequest, type QubitResponse } from '@/lib/api';

export interface BlochState {
  x: number;
  y: number;
  z: number;
  purity: number;
}

export interface QubitState {
  id: number;
  bloch: BlochState;
  rho: [[number, number], [number, number]]; // 2x2 density matrix
  label: string;
}

export interface SimulationState {
  status: 'idle' | 'running' | 'paused' | 'completed' | 'error';
  progress: number;
  pipeline: 'unitary' | 'exact_density' | 'trajectory';
  shots: number;
}

export interface QuantumState {
  // Core state
  qubits: QubitState[];
  simulation: SimulationState;
  
  // UI state
  selectedQubit: number | null;
  endianness: 'little' | 'big';
  compactMode: boolean;
  
  // Circuit input
  qasmCode: string;
  presetCircuit: string;
  
  // Actions
  setQubits: (qubits: QubitState[]) => void;
  updateQubit: (id: number, updates: Partial<QubitState>) => void;
  setSelectedQubit: (id: number | null) => void;
  setSimulationStatus: (status: SimulationState['status']) => void;
  setQasmCode: (code: string) => void;
  setPresetCircuit: (preset: string) => void;
  toggleEndianness: () => void;
  toggleCompactMode: () => void;
  resetSimulation: () => void;
  runSimulation: () => Promise<void>;
}

export const useQuantumStore = create<QuantumState>((set, get) => ({
  // Initial state
  qubits: generateInitialQubits(3),
  simulation: {
    status: 'completed',
    progress: 100,
    pipeline: 'unitary',
    shots: 1024,
  },
  selectedQubit: null,
  endianness: 'little',
  compactMode: false,
  qasmCode: `OPENQASM 2.0;
include "qelib1.inc";

qreg q[3];

// Create GHZ state
h q[0];
cx q[0], q[1];
cx q[1], q[2];`,
  presetCircuit: 'ghz',
  
  // Actions
  setQubits: (qubits) => set({ qubits }),
  
  updateQubit: (id, updates) => set((state) => ({
    qubits: state.qubits.map(qubit => 
      qubit.id === id ? { ...qubit, ...updates } : qubit
    )
  })),
  
  setSelectedQubit: (id) => set({ selectedQubit: id }),
  
  setSimulationStatus: (status) => set((state) => ({
    simulation: { ...state.simulation, status }
  })),
  
  setQasmCode: (code) => set({ qasmCode: code }),
  
  setPresetCircuit: (preset) => set({ presetCircuit: preset }),
  
  toggleEndianness: () => set((state) => ({
    endianness: state.endianness === 'little' ? 'big' : 'little'
  })),
  
  toggleCompactMode: () => set((state) => ({
    compactMode: !state.compactMode
  })),
  
  resetSimulation: () => set((state) => ({
    simulation: { ...state.simulation, status: 'idle', progress: 0 },
    qubits: generateInitialQubits(state.qubits.length)
  })),

  runSimulation: async () => {
    const state = get();
    
    try {
      set((prevState) => ({
        simulation: { 
          ...prevState.simulation, 
          status: 'running', 
          progress: 0 
        }
      }));

      const request: SimulationRequest = {
        qasm_code: state.qasmCode,
        shots: state.simulation.shots,
        // Only override pipeline if explicitly set by user, otherwise let backend choose
        pipeline_override: undefined, // Let backend's smart routing decide
      };

      const response = await quantumAPI.simulate(request);

// Helper function to parse complex numbers from backend
function parseComplexNumber(complexStr: string): number {
  // Backend returns complex numbers as strings like "0.5+0j" or "0.5-0.2j"
  // For density matrices, we usually only need the real part
  if (typeof complexStr === 'string') {
    const match = complexStr.match(/^([+-]?[0-9]*\.?[0-9]+)/);
    return match ? parseFloat(match[1]) : 0;
  }
  return complexStr as number; // fallback if already a number
}

      // Convert backend response to frontend format
      const qubits: QubitState[] = response.qubits.map((qubit: QubitResponse) => ({
        id: qubit.id,
        bloch: {
          x: qubit.bloch_coords[0],
          y: qubit.bloch_coords[1],
          z: qubit.bloch_coords[2],
          purity: qubit.purity,
        },
        rho: [
          [parseComplexNumber(qubit.density_matrix[0][0]), parseComplexNumber(qubit.density_matrix[0][1])],
          [parseComplexNumber(qubit.density_matrix[1][0]), parseComplexNumber(qubit.density_matrix[1][1])]
        ] as [[number, number], [number, number]],
        label: qubit.label,
      }));

      set((prevState) => ({
        qubits,
        simulation: {
          ...prevState.simulation,
          status: 'completed',
          progress: 100,
          pipeline: response.pipeline_used as any,
        }
      }));

    } catch (error) {
      console.error('Simulation failed:', error);
      set((prevState) => ({
        simulation: {
          ...prevState.simulation,
          status: 'error',
          progress: 0,
        }
      }));
      throw error;
    }
  },
}));

function generateInitialQubits(count: number): QubitState[] {
  // Return some interesting initial states that match a GHZ state
  if (count === 3) {
    return [
      {
        id: 0,
        bloch: { x: 0.000, y: 0.000, z: 1.000, purity: 1.000 }, // Entangled
        rho: [[0.5, 0], [0, 0.5]], 
        label: 'Q0',
      },
      {
        id: 1,
        bloch: { x: 0.000, y: 0.000, z: 1.000, purity: 1.000 }, // Entangled
        rho: [[0.5, 0], [0, 0.5]], 
        label: 'Q1',
      },
      {
        id: 2,
        bloch: { x: 0.000, y: 0.800, z: 1.000, purity: 1.000 }, // Different state
        rho: [[0.5, 0], [0, 0.5]], 
        label: 'Q2',
      },
    ];
  }
  
  return Array.from({ length: count }, (_, i) => ({
    id: i,
    bloch: { x: 0, y: 0, z: 1, purity: 1 }, // |0⟩ state
    rho: [[1, 0], [0, 0]], // |0⟩⟨0|
    label: `Q${i}`,
  }));
}

// Preset circuits for quick demos
export const PRESET_CIRCUITS = {
  bell: {
    name: 'Bell State',
    qasm: `OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
h q[0];
cx q[0], q[1];`,
    description: 'Create an entangled Bell state between two qubits',
  },
  ghz: {
    name: 'GHZ State',
    qasm: `OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
h q[0];
cx q[0], q[1];
cx q[1], q[2];`,
    description: 'Three-qubit GHZ entangled state',
  },
  superposition: {
    name: 'Superposition',
    qasm: `OPENQASM 2.0;
include "qelib1.inc";
qreg q[1];
h q[0];`,
    description: 'Single qubit in superposition state',
  },
  random: {
    name: 'Random State',
    qasm: `OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
ry(1.57) q[0];
rx(0.78) q[1];`,
    description: 'Random quantum state for demonstration',
  },
  w_state: {
    name: 'W State',
    qasm: `OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
ry(1.910633236) q[0];
cx q[0], q[1];
ccx q[0], q[1], q[2];
cx q[0], q[1];`,
    description: 'Three-qubit W state with symmetric entanglement',
  },
  deutsch: {
    name: 'Deutsch Algorithm',
    qasm: `OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
x q[1];
h q[0];
h q[1];
cx q[0], q[1];
h q[0];`,
    description: 'Deutsch algorithm demonstration circuit',
  },
  phase_kickback: {
    name: 'Phase Kickback',
    qasm: `OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
h q[0];
x q[1];
h q[1];
cz q[0], q[1];
h q[1];`,
    description: 'Demonstrates phase kickback phenomenon',
  },
  interference: {
    name: 'Quantum Interference',
    qasm: `OPENQASM 2.0;
include "qelib1.inc";
qreg q[1];
h q[0];
s q[0];
h q[0];`,
    description: 'Shows quantum interference with phase gates',
  },
  teleportation: {
    name: 'Quantum Teleportation',
    qasm: `OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
creg c[3];
ry(0.5) q[0];
h q[1];
cx q[1], q[2];
cx q[0], q[1];
h q[0];
measure q[0] -> c[0];
measure q[1] -> c[1];`,
    description: 'Quantum teleportation protocol setup',
  },
  bernstein_vazirani: {
    name: 'Bernstein-Vazirani',
    qasm: `OPENQASM 2.0;
include "qelib1.inc";
qreg q[4];
x q[3];
h q[0];
h q[1];
h q[2];
h q[3];
cx q[0], q[3];
cx q[2], q[3];
h q[0];
h q[1];
h q[2];`,
    description: 'Bernstein-Vazirani algorithm for secret string 101',
  },
  grover_2bit: {
    name: 'Grover Search (2-bit)',
    qasm: `OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
h q[0];
h q[1];
z q[0];
z q[1];
cz q[0], q[1];
h q[0];
h q[1];
x q[0];
x q[1];
cz q[0], q[1];
x q[0];
x q[1];
h q[0];
h q[1];`,
    description: 'Grover search algorithm for 2 qubits',
  },
  qft_3bit: {
    name: 'Quantum Fourier Transform',
    qasm: `OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
x q[0];
h q[2];
cu1(pi/2) q[1], q[2];
cu1(pi/4) q[0], q[2];
h q[1];
cu1(pi/2) q[0], q[1];
h q[0];
swap q[0], q[2];`,
    description: '3-qubit Quantum Fourier Transform',
  },
  cat_state: {
    name: 'Schrödinger Cat State',
    qasm: `OPENQASM 2.0;
include "qelib1.inc";
qreg q[4];
h q[0];
cx q[0], q[1];
cx q[0], q[2];
cx q[0], q[3];`,
    description: 'Four-qubit cat state |0000⟩ + |1111⟩',
  },
  plus_minus: {
    name: 'Plus-Minus States',
    qasm: `OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
h q[0];
x q[1];
h q[1];`,
    description: 'Demonstrates |+⟩ and |-⟩ states',
  },
  bloch_rotations: {
    name: 'Bloch Sphere Rotations',
    qasm: `OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
rx(pi/3) q[0];
ry(pi/4) q[1];
rz(pi/6) q[2];`,
    description: 'Different rotation axes on Bloch sphere',
  },
};