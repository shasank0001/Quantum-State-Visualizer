import { BlochSphere } from './BlochSphere';
import { ExpandedQubitView } from './ExpandedQubitView';
import { useQuantumStore } from '@/store/quantumStore';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { GridIcon, ListIcon } from 'lucide-react';
import { useState } from 'react';

export const CanvasGrid = () => {
  const { 
    qubits, 
    selectedQubit, 
    setSelectedQubit, 
    compactMode, 
    toggleCompactMode,
    endianness,
    simulation 
  } = useQuantumStore();
  
  const [expandedQubit, setExpandedQubit] = useState<number | null>(null);
  
  const sphereSize = compactMode ? 'small' : 'medium';
  const gridCols = compactMode 
    ? 'grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5'
    : 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4';

  const handleQubitClick = (qubitId: number) => {
    setExpandedQubit(qubitId);
    setSelectedQubit(qubitId);
  };

  const handleCloseExpanded = () => {
    setExpandedQubit(null);
  };

  const expandedQubitData = qubits.find(q => q.id === expandedQubit);
  
  return (
    <Card className="quantum-card">
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <h2 className="text-2xl font-bold text-foreground">Quantum States</h2>
            <Badge variant="outline" className="border-quantum-primary text-quantum-primary">
              {qubits.length} Qubit{qubits.length !== 1 ? 's' : ''}
            </Badge>
            <Badge variant="outline" className="border-quantum-secondary text-quantum-secondary">
              {endianness === 'little' ? 'Little' : 'Big'} Endian
            </Badge>
          </div>
          
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={toggleCompactMode}
              className="border-border hover:bg-accent"
            >
              {compactMode ? <ListIcon className="w-4 h-4" /> : <GridIcon className="w-4 h-4" />}
              {compactMode ? 'Detailed' : 'Compact'}
            </Button>
          </div>
        </div>
        
        {/* Qubit Mapping Info */}
        <div className="mb-4 p-3 bg-gradient-quantum-subtle rounded-lg border border-border">
          <div className="text-sm text-muted-foreground">
            <span className="font-semibold text-foreground">Qubit Mapping:</span> 
            {' '}Q0 = {endianness === 'little' ? 'Rightmost' : 'Leftmost'} position
            {qubits.length > 1 && (
              <span className="ml-2">
                (Q0 → Q{qubits.length - 1} {endianness === 'little' ? 'right to left' : 'left to right'})
              </span>
            )}
          </div>
        </div>
        
        {/* Simulation Status */}
        {simulation.status !== 'idle' && (
          <div className="mb-4 p-3 bg-gradient-quantum-subtle rounded-lg border border-border">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${
                simulation.status === 'running' ? 'bg-quantum-warning animate-quantum-pulse' :
                simulation.status === 'completed' ? 'bg-quantum-success' :
                simulation.status === 'error' ? 'bg-destructive' :
                'bg-muted'
              }`} />
              <span className="text-sm font-semibold text-foreground capitalize">
                {simulation.status}
              </span>
              {simulation.status === 'running' && (
                <span className="text-xs text-muted-foreground">
                  (Pipeline: {simulation.pipeline})
                </span>
              )}
            </div>
          </div>
        )}
        
        {/* Bloch Spheres Grid */}
        <div className={`grid gap-4 ${gridCols}`}>
          {qubits.map((qubit) => (
            <div key={qubit.id} className="animate-fade-in-up">
              <BlochSphere
                qubit={qubit}
                isSelected={selectedQubit === qubit.id}
                onSelect={() => handleQubitClick(qubit.id)}
                size={sphereSize}
              />
            </div>
          ))}
        </div>

        {/* Expanded Qubit View Modal */}
        {expandedQubitData && (
          <ExpandedQubitView
            qubit={expandedQubitData}
            isOpen={expandedQubit !== null}
            onClose={handleCloseExpanded}
          />
        )}
        
        {/* Empty State */}
        {qubits.length === 0 && (
          <div className="text-center py-12">
            <div className="text-muted-foreground">
              <p className="text-lg mb-2">No qubits to display</p>
              <p className="text-sm">Run a quantum circuit to see the Bloch sphere visualization</p>
            </div>
          </div>
        )}
        
        {/* Selection Hint */}
        {qubits.length > 0 && selectedQubit === null && (
          <div className="mt-4 text-center text-sm text-muted-foreground">
            Click on a Bloch sphere to open the interactive Q-sphere view
          </div>
        )}
      </div>
    </Card>
  );
};