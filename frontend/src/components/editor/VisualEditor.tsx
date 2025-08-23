import { GatePalette } from './palette/GatePalette.tsx';
import { EditorToolbar } from './toolbar/EditorToolbar.tsx';
import { TimelineGrid } from './timeline/TimelineGrid.tsx';
import { CodePreview } from './CodePreview.tsx';
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
    <div className="w-full animate-in fade-in duration-500">
      {visualReadOnly && (
        <div className="mb-3 rounded border border-yellow-500/40 bg-yellow-500/10 px-3 py-2 text-xs text-yellow-700 animate-in slide-in-from-top duration-300">
          Visual editor is read-only because the current QASM contains unsupported constructs.
        </div>
      )}
      
      {pendingControl !== null && (
        <div className="mb-3 rounded border border-blue-500/40 bg-blue-500/10 px-3 py-2 text-xs text-blue-700 dark:text-blue-300 animate-in slide-in-from-top duration-300">
          Two-qubit gate placement in progress. Press <kbd className="px-1 py-0.5 bg-blue-200 dark:bg-blue-800 rounded text-xs">Esc</kbd> to cancel.
        </div>
      )}
      
      <div className="flex gap-6 items-start transition-all duration-500 ease-in-out">
        <div className="w-64 shrink-0 transition-all duration-300">
          <GatePalette />
        </div>
        <div className="flex-1 grid grid-cols-1 xl:grid-cols-2 gap-6 transition-all duration-500 ease-in-out">
          <div className="space-y-4 transition-all duration-300">
            <EditorToolbar />
            <TimelineGrid />
          </div>
          <div className="min-h-[400px] transition-all duration-300 animate-in slide-in-from-right duration-700">
            <CodePreview />
          </div>
        </div>
      </div>
    </div>
  );
};
