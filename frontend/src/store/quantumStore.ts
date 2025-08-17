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
        pipeline_override: state.simulation.pipeline,
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
};