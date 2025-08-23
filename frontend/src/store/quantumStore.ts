import { create } from 'zustand';
import { quantumAPI, type SimulationRequest, type QubitResponse } from '@/lib/api';
import { QASMValidator, type QASMValidationResult, type VisualCircuitValidationResult } from '@/lib/qasmValidator';

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
  editorTab: 'visual' | 'code';
  codeEditorMode: 'simple' | 'monaco';
  monacoEditorFullscreen: boolean;
  uploadedFileName: string | null;

  // Visual editor state
  visualCircuit: {
    qubits: 1|2|3|4;
    steps: Array<Record<number, { id: string; type: 'H'|'X'|'Z'|'S'|'T'|'CNOT'|'CZ'; targets: number[]; controls?: number[]; role?: 'control'|'target'; linkId?: string }>>;
  };
  visualReadOnly: boolean;
  activeGate: null | 'H'|'X'|'Z'|'S'|'T'|'CNOT'|'CZ';
  pendingControl: number | null;
  
  // Validation state
  qasmValidation: QASMValidationResult | null;
  visualValidation: VisualCircuitValidationResult | null;
  
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

  // Visual editor actions
  setVisualQubits: (n: 1|2|3|4) => void;
  addColumn: () => void;
  removeColumn: () => void;
  setVisualReadOnly: (ro: boolean) => void;
  compileVisualToQASM: () => string;
  selectActiveGate: (g: QuantumState['activeGate']) => void;
  clearPendingControl: () => void;
  handleCellClick: (row: number, col: number) => void;
  setEditorTab: (tab: 'visual' | 'code') => void;

  // Code editor actions
  setCodeEditorMode: (mode: 'simple' | 'monaco') => void;
  toggleMonacoFullscreen: () => void;
  setUploadedFileName: (filename: string | null) => void;
  loadFileContent: (content: string, filename: string) => void;
  
  // Validation actions
  validateQASM: (qasm?: string) => QASMValidationResult;
  validateVisualCircuit: () => VisualCircuitValidationResult;
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
  editorTab: 'visual',
  codeEditorMode: 'simple',
  monacoEditorFullscreen: false,
  uploadedFileName: null,

  visualCircuit: {
    qubits: 3,
    steps: Array.from({ length: 15 }, () => ({})),
  },
  visualReadOnly: false,
  activeGate: null,
  pendingControl: null,
  
  // Validation state
  qasmValidation: null,
  visualValidation: null,
  
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

      // Force compilation of visual circuit if in visual mode to ensure QASM is up-to-date
      let qasmToUse = state.qasmCode;
      if (state.editorTab === 'visual') {
        console.log('Compiling visual circuit to QASM before simulation...');
        qasmToUse = get().compileVisualToQASM();
      }

      const request: SimulationRequest = {
        qasm_code: qasmToUse,
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

  // Visual editor actions
  setVisualQubits: (n) => set((state) => {
    const clamped = Math.max(1, Math.min(4, n)) as 1|2|3|4;
    // prune any nodes beyond the new qubit count
    const prunedSteps = state.visualCircuit.steps.map((col) => {
      const entries = Object.entries(col).filter(([row]) => Number(row) < clamped);
      return Object.fromEntries(entries);
    });
    return { visualCircuit: { ...state.visualCircuit, qubits: clamped, steps: prunedSteps } };
  }),

  setEditorTab: (tab) => set({ editorTab: tab }),
  
  // Code editor actions
  setCodeEditorMode: (mode) => set({ codeEditorMode: mode }),
  toggleMonacoFullscreen: () => set((state) => ({ monacoEditorFullscreen: !state.monacoEditorFullscreen })),
  setUploadedFileName: (filename) => set({ uploadedFileName: filename }),
  loadFileContent: (content, filename) => set({ 
    qasmCode: content, 
    uploadedFileName: filename,
    codeEditorMode: 'simple' // Switch back to simple editor after upload
  }),
  addColumn: () => set((state) => ({
    visualCircuit: { ...state.visualCircuit, steps: [...state.visualCircuit.steps, {}] }
  })),
  removeColumn: () => set((state) => ({
    visualCircuit: { ...state.visualCircuit, steps: state.visualCircuit.steps.length > 1 ? state.visualCircuit.steps.slice(0, -1) : state.visualCircuit.steps }
  })),
  setVisualReadOnly: (ro) => set({ visualReadOnly: ro }),
  compileVisualToQASM: () => {
    const state = get();
    const N = state.visualCircuit.qubits;
    
    // First validate the visual circuit
    const visualValidation = QASMValidator.validateVisualCircuit(state.visualCircuit);
    set({ visualValidation });
    
    if (!visualValidation.isValid) {
      console.error('Visual circuit validation failed:', visualValidation.errors);
      // Continue compilation but with warnings
    }
    
    const lines: string[] = [
      'OPENQASM 2.0;',
      'include "qelib1.inc";',
      `qreg q[${N}];`
    ];
    
    const errors: string[] = [];
    
    // iterate columns with enhanced validation
    state.visualCircuit.steps.forEach((col, colIdx) => {
      Object.entries(col).forEach(([rowIdx, node]) => {
        const i = Number(rowIdx);
        if (i >= N) {
          errors.push(`Qubit index ${i} out of bounds (max: ${N-1}) at column ${colIdx + 1}`);
          return;
        }
        
        // For two-qubit gates, emit only once (on control role or if no role)
        if ((node.type === 'CNOT' || node.type === 'CZ') && node.role === 'target') return;
        
        try {
          switch (node.type) {
            case 'H': 
              if (i < 0 || i >= N) {
                errors.push(`H gate qubit index ${i} out of bounds at column ${colIdx + 1}`);
                break;
              }
              lines.push(`h q[${i}];`); 
              break;
            case 'X': 
              if (i < 0 || i >= N) {
                errors.push(`X gate qubit index ${i} out of bounds at column ${colIdx + 1}`);
                break;
              }
              lines.push(`x q[${i}];`); 
              break;
            case 'Z': 
              if (i < 0 || i >= N) {
                errors.push(`Z gate qubit index ${i} out of bounds at column ${colIdx + 1}`);
                break;
              }
              lines.push(`z q[${i}];`); 
              break;
            case 'S': 
              if (i < 0 || i >= N) {
                errors.push(`S gate qubit index ${i} out of bounds at column ${colIdx + 1}`);
                break;
              }
              lines.push(`s q[${i}];`); 
              break;
            case 'T': 
              if (i < 0 || i >= N) {
                errors.push(`T gate qubit index ${i} out of bounds at column ${colIdx + 1}`);
                break;
              }
              lines.push(`t q[${i}];`); 
              break;
            case 'CNOT': 
              if (!node.controls || !node.targets || !Array.isArray(node.controls) || !Array.isArray(node.targets)) {
                errors.push(`Invalid CNOT at column ${colIdx + 1}, row ${i + 1}: missing or malformed controls/targets`);
                break;
              }
              if (node.controls.length === 0 || node.targets.length === 0) {
                errors.push(`Invalid CNOT at column ${colIdx + 1}, row ${i + 1}: empty controls or targets array`);
                break;
              }
              const cnotControl = node.controls[0];
              const cnotTarget = node.targets[0];
              if (typeof cnotControl !== 'number' || typeof cnotTarget !== 'number') {
                errors.push(`Invalid CNOT at column ${colIdx + 1}: control or target is not a number`);
                break;
              }
              if (cnotControl < 0 || cnotControl >= N) {
                errors.push(`CNOT control Q${cnotControl} out of bounds at column ${colIdx + 1} (valid: 0-${N-1})`);
                break;
              }
              if (cnotTarget < 0 || cnotTarget >= N) {
                errors.push(`CNOT target Q${cnotTarget} out of bounds at column ${colIdx + 1} (valid: 0-${N-1})`);
                break;
              }
              if (cnotControl === cnotTarget) {
                errors.push(`CNOT control and target cannot be the same qubit (Q${cnotControl}) at column ${colIdx + 1}`);
                break;
              }
              lines.push(`cx q[${cnotControl}], q[${cnotTarget}];`); 
              break;
            case 'CZ': 
              if (!node.controls || !node.targets || !Array.isArray(node.controls) || !Array.isArray(node.targets)) {
                errors.push(`Invalid CZ at column ${colIdx + 1}, row ${i + 1}: missing or malformed controls/targets`);
                break;
              }
              if (node.controls.length === 0 || node.targets.length === 0) {
                errors.push(`Invalid CZ at column ${colIdx + 1}, row ${i + 1}: empty controls or targets array`);
                break;
              }
              const czControl = node.controls[0];
              const czTarget = node.targets[0];
              if (typeof czControl !== 'number' || typeof czTarget !== 'number') {
                errors.push(`Invalid CZ at column ${colIdx + 1}: control or target is not a number`);
                break;
              }
              if (czControl < 0 || czControl >= N) {
                errors.push(`CZ control Q${czControl} out of bounds at column ${colIdx + 1} (valid: 0-${N-1})`);
                break;
              }
              if (czTarget < 0 || czTarget >= N) {
                errors.push(`CZ target Q${czTarget} out of bounds at column ${colIdx + 1} (valid: 0-${N-1})`);
                break;
              }
              if (czControl === czTarget) {
                errors.push(`CZ control and target cannot be the same qubit (Q${czControl}) at column ${colIdx + 1}`);
                break;
              }
              lines.push(`cz q[${czControl}], q[${czTarget}];`); 
              break;
            default:
              errors.push(`Unknown gate type: ${node.type} at column ${colIdx + 1}, row ${i + 1}`);
          }
        } catch (error) {
          errors.push(`Error processing gate at column ${colIdx + 1}, row ${i + 1}: ${error}`);
        }
      });
    });
    
    const qasm = lines.join('\n');
    
    // Validate the generated QASM
    const qasmValidation = QASMValidator.validateQASM(qasm);
    set({ qasmValidation });
    
    // Log compilation results
    if (errors.length > 0) {
      console.error('Visual circuit compilation errors:', errors);
    }
    if (qasmValidation.errors.length > 0) {
      console.error('Generated QASM validation errors:', qasmValidation.errors);
    }
    if (qasmValidation.warnings.length > 0) {
      console.warn('Generated QASM validation warnings:', qasmValidation.warnings);
    }
    
    set({ qasmCode: qasm });
    return qasm;
  },
  selectActiveGate: (g) => set({ activeGate: g, pendingControl: null }),
  clearPendingControl: () => set({ pendingControl: null }),
  
  validateQASM: (qasmCode: string) => {
    const validation = QASMValidator.validateQASM(qasmCode);
    set({ qasmValidation: validation });
    return validation;
  },

  validateVisualCircuit: () => {
    const state = get();
    const validation = QASMValidator.validateVisualCircuit(state.visualCircuit);
    set({ visualValidation: validation });
    return validation;
  },
  handleCellClick: (row, col) => set((state) => {
    if (state.visualReadOnly) return {} as any;
    const steps = state.visualCircuit.steps.slice();
    const colMap = { ...steps[col] };
    const existing = colMap[row];
    
    // If clicking an existing gate: delete it (and linked target/control if any)
    if (existing) {
      if ((existing.type === 'CNOT' || existing.type === 'CZ') && existing.linkId) {
        // Remove linked peer
        const peerRow = existing.role === 'control' ? existing.targets?.[0] : existing.controls?.[0];
        if (peerRow !== undefined) {
          const peerMap = { ...colMap };
          delete peerMap[peerRow];
          delete peerMap[row];
          steps[col] = peerMap;
        } else {
          delete colMap[row];
          steps[col] = colMap;
        }
      } else {
        delete colMap[row];
        steps[col] = colMap;
      }
      return { visualCircuit: { ...state.visualCircuit, steps }, pendingControl: null } as any;
    }
    
    // No existing gate; place new based on activeGate
    const g = state.activeGate;
    if (!g) return {} as any;
    
    // Prevent overlap
    if (colMap[row]) return {} as any;
    
    const id = `${g}-${col}-${Date.now()}`;
    
    if (g === 'CNOT' || g === 'CZ') {
      // Two-step selection: first control, then target
      if (state.pendingControl === null) {
        // First click: set control qubit
        return { pendingControl: row } as any;
      } else {
        const control = state.pendingControl;
        const target = row;
        
        // Validation: control and target cannot be the same
        if (target === control) {
          console.warn(`${g} control and target cannot be the same qubit (Q${control})`);
          return { pendingControl: null } as any; // Clear pending state
        }
        
        // Validation: target cell must be empty
        if (colMap[target]) {
          console.warn(`Target position Q${target} is already occupied`);
          return { pendingControl: null } as any; // Clear pending state
        }
        
        // Validation: control cell must also be empty
        if (colMap[control]) {
          console.warn(`Control position Q${control} is already occupied`);
          return { pendingControl: null } as any; // Clear pending state
        }
        
        // All validations passed: place the two-qubit gate
        const linkId = id;
        colMap[control] = { 
          id, 
          type: g, 
          controls: [control], 
          targets: [target], 
          role: 'control', 
          linkId 
        };
        colMap[target] = { 
          id, 
          type: g, 
          controls: [control], 
          targets: [target], 
          role: 'target', 
          linkId 
        };
        steps[col] = colMap;
        
        return { 
          visualCircuit: { ...state.visualCircuit, steps }, 
          pendingControl: null 
        } as any;
      }
    } else {
      // Single-qubit gate
      colMap[row] = { id, type: g, targets: [row] };
      steps[col] = colMap;
      return { visualCircuit: { ...state.visualCircuit, steps } } as any;
    }
  }),
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