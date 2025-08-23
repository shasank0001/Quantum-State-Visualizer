import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { useQuantumStore } from '@/store/quantumStore';

export const EditorToolbar = () => {
  const { 
    visualCircuit, 
    setVisualQubits, 
    addColumn, 
    removeColumn, 
    pendingControl,
    clearPendingControl 
  } = useQuantumStore();
  
  const handleQubitCountChange = (n: 1|2|3|4) => {
    if (pendingControl !== null) {
      clearPendingControl(); // Clear pending state when changing qubit count
    }
    setVisualQubits(n);
  };
  
  return (
    <div className="flex items-center justify-between rounded border border-border bg-muted/30 p-2">
      <div className="flex items-center gap-3">
        <Label className="text-xs">Qubits</Label>
        <div className="inline-flex rounded border border-border overflow-hidden">
          {[1,2,3,4].map(n => (
            <button
              key={n}
              className={`px-2 py-1 text-xs transition-colors ${
                visualCircuit.qubits === n 
                  ? 'bg-background text-foreground shadow-sm' 
                  : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
              }`}
              onClick={() => handleQubitCountChange(n as 1|2|3|4)}
              disabled={pendingControl !== null && pendingControl >= n}
              title={
                pendingControl !== null && pendingControl >= n 
                  ? `Cannot reduce qubits while Q${pendingControl} is selected as control`
                  : `Set circuit to ${n} qubit${n > 1 ? 's' : ''}`
              }
            >
              {n}
            </button>
          ))}
        </div>
        
        {pendingControl !== null && (
          <Badge variant="secondary" className="text-xs">
            Control: Q{pendingControl}
          </Badge>
        )}
      </div>
      
      <div className="flex items-center gap-2">
        <Button 
          size="sm" 
          variant="outline" 
          className="border-border" 
          onClick={() => {
            if (pendingControl !== null) clearPendingControl();
            addColumn();
          }}
        >
          + Column
        </Button>
        <Button 
          size="sm" 
          variant="outline" 
          className="border-border" 
          onClick={() => {
            if (pendingControl !== null) clearPendingControl();
            removeColumn();
          }}
        >
          - Column
        </Button>
      </div>
    </div>
  );
};
