import { GatePalette } from './palette/GatePalette.tsx';
import { EditorToolbar } from './toolbar/EditorToolbar.tsx';
import { TimelineGrid } from './timeline/TimelineGrid.tsx';
import { useQuantumStore } from '@/store/quantumStore';
import { useEffect } from 'react';

export const VisualEditor = () => {
  const { 
    visualReadOnly, 
    visualCircuit, 
    compileVisualToQASM, 
    clearPendingControl, 
    pendingControl 
  } = useQuantumStore();
  
  // Auto-compile to QASM when circuit changes
  useEffect(() => {
    compileVisualToQASM();
  }, [visualCircuit.steps, visualCircuit.qubits]);
  
  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && pendingControl !== null) {
        clearPendingControl();
      }
    };
    
    document.addEventListener('keydown', handleKeyPress);
    return () => document.removeEventListener('keydown', handleKeyPress);
  }, [pendingControl, clearPendingControl]);
  
  return (
    <div className="w-full">
      {visualReadOnly && (
        <div className="mb-3 rounded border border-yellow-500/40 bg-yellow-500/10 px-3 py-2 text-xs text-yellow-700">
          Visual editor is read-only because the current QASM contains unsupported constructs.
        </div>
      )}
      
      {pendingControl !== null && (
        <div className="mb-3 rounded border border-blue-500/40 bg-blue-500/10 px-3 py-2 text-xs text-blue-700 dark:text-blue-300">
          Two-qubit gate placement in progress. Press <kbd className="px-1 py-0.5 bg-blue-200 dark:bg-blue-800 rounded text-xs">Esc</kbd> to cancel.
        </div>
      )}
      
      <div className="flex gap-6 items-start">
        <div className="w-64 shrink-0">
          <GatePalette />
        </div>
        <div className="flex-1 space-y-4">
          <EditorToolbar />
          <TimelineGrid />
        </div>
      </div>
    </div>
  );
};
