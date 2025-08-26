import { EditorPanel } from '@/components/EditorPanel';
import { CanvasGrid } from '@/components/CanvasGrid';
import { Inspector } from '@/components/Inspector';
import { ControlsBar } from '@/components/ControlsBar';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useQuantumStore } from '@/store/quantumStore';
import { AtomIcon, InfoIcon } from 'lucide-react';
import { ThemeToggle } from '@/components/ThemeToggle';

const Index = () => {
  const { qubits, simulation, editorTab, codeEditorMode } = useQuantumStore();
  
  // Determine if we need expanded layout for Monaco editor
  const needsExpandedLayout = editorTab === 'code' && codeEditorMode === 'monaco';
  
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-gradient-quantum-subtle">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-quantum flex items-center justify-center">
                <AtomIcon className="w-5 h-5 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-foreground">Quantum State Visualizer</h1>
                <p className="text-sm text-muted-foreground">Interactive Bloch Sphere Visualization</p>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <Badge variant="outline" className="border-quantum-primary text-quantum-primary">
                {qubits.length} Qubit{qubits.length !== 1 ? 's' : ''}
              </Badge>
              <Badge 
                variant={simulation.status === 'completed' ? 'default' : 'secondary'}
                className={simulation.status === 'running' ? 'animate-quantum-pulse' : ''}
              >
                {simulation.status.toUpperCase()}
              </Badge>
              <Button variant="ghost" size="sm" className="hover:bg-accent">
                <InfoIcon className="w-4 h-4" />
              </Button>
              <ThemeToggle />
            </div>
          </div>
        </div>
      </header>
      
      {/* Main Content */}
      <main className="container mx-auto px-4 py-6">
        <div className={`transition-all duration-700 ease-in-out ${
          editorTab === 'visual' 
            ? 'flex flex-col gap-6 mb-6' 
            : needsExpandedLayout
            ? 'flex flex-col gap-6 mb-6'  // Full width for Monaco editor
            : 'grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6'
        }`}>
          <div className={`transition-all duration-700 ease-in-out ${
            editorTab === 'visual' 
              ? '' 
              : needsExpandedLayout 
              ? '' 
              : 'lg:col-span-1'
          }`}>
            <EditorPanel />
          </div>
          <div className={`transition-all duration-700 ease-in-out ${
            editorTab === 'visual' 
              ? '' 
              : needsExpandedLayout 
              ? '' 
              : 'lg:col-span-2'
          }`}>
            <CanvasGrid />
          </div>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Inspector */}
          <div className="lg:col-span-1">
            <Inspector />
          </div>
          
          {/* Controls Bar */}
          <div className="lg:col-span-2">
            <ControlsBar />
          </div>
        </div>
      </main>
      
      {/* Footer */}
      <footer className="border-t border-border bg-gradient-quantum-subtle mt-12">
        <div className="container mx-auto px-4 py-6">
          <div className="text-center text-sm text-muted-foreground">
            <p>Quantum State Visualizer - Interactive quantum computing education tool</p>
            <p className="mt-1">Built with React Three Fiber • OpenQASM 2.0 Compatible</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Index;
