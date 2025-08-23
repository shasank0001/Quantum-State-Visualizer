import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useQuantumStore } from '@/store/quantumStore';

const gates = [
  { type: 'H', label: 'H', description: 'Hadamard' },
  { type: 'X', label: 'X', description: 'Pauli-X' },
  { type: 'Z', label: 'Z', description: 'Pauli-Z' },
  { type: 'S', label: 'S', description: 'Phase' },
  { type: 'T', label: 'T', description: 'T-gate' },
  { type: 'CNOT', label: 'CNOT', description: 'Controlled-X' },
  { type: 'CZ', label: 'CZ', description: 'Controlled-Z' },
] as const;

export const GatePalette = () => {
  const { activeGate, selectActiveGate, pendingControl, clearPendingControl } = useQuantumStore();
  
  const isTwoQubitGate = (gateType: string) => gateType === 'CNOT' || gateType === 'CZ';
  
  return (
    <div className="space-y-3">
      <div className="text-sm font-medium text-foreground">Gates</div>
      
      {/* Two-qubit gate status indicator */}
      {pendingControl !== null && (
        <div className="rounded-lg bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 p-3">
          <div className="flex items-center justify-between mb-2">
            <div className="text-xs font-semibold text-blue-700 dark:text-blue-300">
              {activeGate} Gate Placement
            </div>
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={clearPendingControl}
              className="h-6 px-2 text-xs"
            >
              Cancel
            </Button>
          </div>
          <div className="text-xs text-blue-600 dark:text-blue-400 space-y-1">
            <div>✓ Control: Q{pendingControl}</div>
            <div className="text-blue-500 dark:text-blue-300">→ Click target qubit</div>
          </div>
        </div>
      )}
      
      <div className="grid grid-cols-2 gap-2">
        {gates.map((g) => (
          <div key={g.type} className="relative">
            <Button 
              variant={activeGate === g.type ? 'default' : 'outline'} 
              size="sm" 
              className={`w-full border-border ${
                activeGate === g.type && isTwoQubitGate(g.type) 
                  ? 'ring-2 ring-blue-400 dark:ring-blue-600' 
                  : ''
              }`}
              onClick={() => selectActiveGate(activeGate === g.type ? null : g.type)}
              draggable
              onDragStart={(e) => {
                try {
                  e.dataTransfer?.setData('text/gate', g.type);
                } catch {}
              }}
            >
              {g.label}
              {isTwoQubitGate(g.type) && (
                <Badge variant="secondary" className="ml-1 text-xs px-1 py-0">
                  2Q
                </Badge>
              )}
            </Button>
            
            {/* Gate description tooltip */}
            <div className="absolute z-10 invisible group-hover:visible bg-popover text-popover-foreground text-xs p-1 rounded shadow-md -top-8 left-1/2 transform -translate-x-1/2 whitespace-nowrap">
              {g.description}
            </div>
          </div>
        ))}
      </div>
      
      <div className="text-xs text-muted-foreground space-y-1">
        <p>• Single-qubit: Click to place</p>
        <p>• Two-qubit: Click control → target</p>
        {activeGate && isTwoQubitGate(activeGate) && (
          <p className="text-blue-600 dark:text-blue-400 font-medium">
            {pendingControl === null ? '1. Select control qubit' : '2. Select target qubit'}
          </p>
        )}
      </div>
    </div>
  );
};
