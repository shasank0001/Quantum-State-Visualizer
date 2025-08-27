import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useQuantumStore } from '@/store/quantumStore';
import { Info } from 'lucide-react';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { GATE_METADATA } from '../gates';

const gates = GATE_METADATA;

type Props = {
  onShowInfo?: (type: typeof gates[number]['type']) => void;
};

export const GatePalette = ({ onShowInfo }: Props) => {
  const { activeGate, selectActiveGate, pendingControl, clearPendingControl } = useQuantumStore();
  
  const isTwoQubitGate = (gateType: string) => {
    const meta = gates.find(g => g.type === (gateType as any));
    return Boolean(meta?.twoQ);
  };
  
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
      
      <TooltipProvider>
      <div className="grid grid-cols-2 gap-2">
        {gates.map((g) => (
          <div key={g.type} className="relative group">
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
              <span className="flex-1 text-left">{g.label}</span>
              <Tooltip>
                <TooltipTrigger asChild>
                  <span
                    role="button"
                    tabIndex={0}
                    className="h-6 w-6 ml-1 inline-flex items-center justify-center rounded-md hover:bg-accent text-muted-foreground"
                    onClick={(e) => { e.stopPropagation(); onShowInfo?.(g.type); }}
                    onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); e.stopPropagation(); onShowInfo?.(g.type); } }}
                    aria-label={`About ${g.name}`}
                  >
                    <Info className="w-3.5 h-3.5" />
                  </span>
                </TooltipTrigger>
                <TooltipContent side="right" className="max-w-[220px]">
                  <div className="text-xs space-y-1">
                    <div className="font-medium">{g.name} ({g.label})</div>
                    <div className="text-muted-foreground">{g.description}</div>
                    <div className="bg-muted rounded px-1.5 py-0.5 font-mono">{g.qasm}</div>
                  </div>
                </TooltipContent>
              </Tooltip>
              {isTwoQubitGate(g.type) && (
                <Badge variant="secondary" className="ml-1 text-xs px-1 py-0">
                  2Q
                </Badge>
              )}
            </Button>
          </div>
        ))}
      </div>
      </TooltipProvider>
      
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
