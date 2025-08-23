import { useQuantumStore } from '@/store/quantumStore';

export const TimelineGrid = () => {
  const { 
    visualCircuit, 
    handleCellClick, 
    visualReadOnly, 
    selectActiveGate, 
    pendingControl, 
    activeGate 
  } = useQuantumStore();
  
  const cols = visualCircuit.steps.length;
  const rows = visualCircuit.qubits;
  
  const renderCell = (r: number, c: number) => {
    const node = visualCircuit.steps[c][r];
    if (!node) return null;
    const base = 'inline-flex items-center justify-center w-full h-full text-xs';
    if (node.type === 'CNOT') {
      // control: filled dot; target: plus symbol
      if (node.role === 'control') return <div className={base}>●</div>;
      if (node.role === 'target') return <div className={base}>⊕</div>;
    }
    if (node.type === 'CZ') {
      if (node.role === 'control' || node.role === 'target') return <div className={base}>Z</div>;
    }
    return <div className={base}>{node.type}</div>;
  };

  const getCellClass = (r: number, c: number) => {
    const node = visualCircuit.steps[c][r];
    let baseClass = 'relative h-12 border-t border-l border-border';
    
    if (visualReadOnly) {
      return `${baseClass} bg-muted/30`;
    }
    
    // Pending control highlight
    if (pendingControl === r && activeGate && (activeGate === 'CNOT' || activeGate === 'CZ')) {
      baseClass += ' bg-blue-100 dark:bg-blue-900/30 border-blue-300 dark:border-blue-600 ring-1 ring-blue-400 dark:ring-blue-500';
    }
    // Occupied cell
    else if (node) {
      baseClass += ' bg-accent/50';
    }
    // Hoverable empty cell
    else {
      baseClass += ' hover:bg-accent/30 cursor-pointer';
    }
    
    return baseClass;
  };

  return (
    <div className="w-full overflow-auto rounded border border-border">
      <table className="w-full border-collapse">
        <thead>
          <tr>
            <th className="sticky left-0 bg-muted/50 p-2 text-left text-xs font-medium text-muted-foreground border-b border-border">Qubits</th>
            {Array.from({ length: cols }).map((_, c) => (
              <th key={c} className="min-w-14 border-b border-border p-1.5 text-center text-[10px] text-muted-foreground">{c+1}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {Array.from({ length: rows }).map((_, r) => (
            <tr key={r}>
              <td className="sticky left-0 bg-background border-t border-border px-2 py-1 text-xs">
                Q{r}
                {pendingControl === r && (
                  <span className="ml-1 text-xs text-blue-600 dark:text-blue-400 font-bold">●</span>
                )}
              </td>
              {Array.from({ length: cols }).map((_, c) => {
                // optional connector: draw a thin vertical line between control and target for 2q gates
                const node = visualCircuit.steps[c][r];
                let drawConnector = false;
                const colMap = visualCircuit.steps[c];
                for (const key in colMap) {
                  const n = colMap[key as any];
                  if (n && (n.type === 'CNOT' || n.type === 'CZ') && n.linkId && n.role === 'control') {
                    const control = n.controls?.[0];
                    const target = n.targets?.[0];
                    if (control !== undefined && target !== undefined) {
                      const [minR, maxR] = control < target ? [control, target] : [target, control];
                      if (r > minR && r < maxR) { drawConnector = true; break; }
                    }
                  }
                }
                
                return (
                  <td 
                    key={`${r}-${c}`} 
                    className={getCellClass(r, c)}
                    onClick={() => handleCellClick(r, c)}
                    onDragOver={(e) => { if (!visualReadOnly) e.preventDefault(); }}
                    onDrop={(e) => {
                      if (visualReadOnly) return;
                      const gate = e.dataTransfer?.getData('text/gate') as any;
                      if (gate) {
                        selectActiveGate(gate);
                        handleCellClick(r, c);
                      }
                    }}
                    title={
                      visualReadOnly 
                        ? 'Read-only mode' 
                        : node 
                          ? `${node.type} gate - Click to remove`
                          : pendingControl === r 
                            ? 'Control qubit selected'
                            : `Click to place ${activeGate || 'gate'}`
                    }
                  >
                    {renderCell(r, c)}
                    {drawConnector && (
                      <div className="pointer-events-none absolute left-1/2 top-0 h-full w-px -translate-x-1/2 bg-foreground/50" />
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
      
      {/* Status bar */}
      {(pendingControl !== null || activeGate) && (
        <div className="border-t border-border bg-muted/30 p-2 text-xs text-muted-foreground">
          {pendingControl !== null ? (
            <span className="text-blue-600 dark:text-blue-400">
              {activeGate} gate: Control Q{pendingControl} selected, click target qubit
            </span>
          ) : activeGate ? (
            <span>
              {activeGate === 'CNOT' || activeGate === 'CZ' 
                ? `${activeGate} gate: Click control qubit first`
                : `${activeGate} gate: Click any cell to place`}
            </span>
          ) : null}
        </div>
      )}
    </div>
  );
};
