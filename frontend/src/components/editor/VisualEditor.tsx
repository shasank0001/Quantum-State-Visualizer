import { GatePalette } from './palette/GatePalette.tsx';
import { EditorToolbar } from './toolbar/EditorToolbar.tsx';
import { TimelineGrid } from './timeline/TimelineGrid.tsx';
import { CodePreview } from './CodePreview.tsx';
import { useQuantumStore } from '@/store/quantumStore';
import { useEffect, useState } from 'react';
import { GATE_METADATA, GateMeta } from './gates.ts';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ExternalLink, X } from 'lucide-react';

export const VisualEditor = () => {
  const { 
    visualReadOnly, 
    visualCircuit, 
    compileVisualToQASM, 
    clearPendingControl, 
    pendingControl 
  } = useQuantumStore();
  const [helperGate, setHelperGate] = useState<GateMeta | null>(null);
  const [showHelperPanel, setShowHelperPanel] = useState<boolean>(true);
  
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
          <GatePalette onShowInfo={(type) => {
            const meta = GATE_METADATA.find(m => m.type === type) || null;
            setHelperGate(meta);
            // Ensure the helper panel is visible when a gate is selected
            setShowHelperPanel(true);
          }} />
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
        {/* Gate Helper Panel */}
        {showHelperPanel && (
          <div className="hidden xl:block w-80 shrink-0">
            <Card className="p-3 sticky top-4">
              <div className="flex items-center justify-between mb-2">
                <div className="text-sm font-semibold">Gate Helper</div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6"
                  onClick={() => setShowHelperPanel(false)}
                  aria-label="Close gate helper"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
              {helperGate ? (
                <div className="space-y-2 text-sm">
                  <div className="font-medium">{helperGate.name} ({helperGate.label})</div>
                  <div className="text-muted-foreground">{helperGate.description}</div>
                  <div className="bg-muted rounded px-2 py-1 font-mono text-xs">{helperGate.qasm}</div>
                  {helperGate.details && (
                    <div className="text-xs text-muted-foreground">{helperGate.details}</div>
                  )}
                  {helperGate.matrix && (
                    <div>
                      <div className="text-xs font-medium mb-1">Matrix</div>
                      <div className="bg-muted rounded px-2 py-1 font-mono text-xs whitespace-pre-wrap">{helperGate.matrix}</div>
                    </div>
                  )}
                  {helperGate.learnUrl && (
                    <Button asChild variant="link" className="px-0 h-auto text-xs">
                      <a href={helperGate.learnUrl} target="_blank" rel="noreferrer">
                        Learn more <ExternalLink className="w-3 h-3 ml-1" />
                      </a>
                    </Button>
                  )}
                </div>
              ) : (
                <div className="text-xs text-muted-foreground">Hover the info icon on a gate to see details here.</div>
              )}
            </Card>
          </div>
        )}
      </div>
    </div>
  );
};
