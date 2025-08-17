import { Card } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useQuantumStore, PRESET_CIRCUITS } from '@/store/quantumStore';
import { PlayIcon, PauseIcon, SquareIcon, InfoIcon } from 'lucide-react';

export const EditorPanel = () => {
  const { 
    qasmCode, 
    setQasmCode, 
    presetCircuit, 
    setPresetCircuit,
    simulation,
    setSimulationStatus,
    resetSimulation,
    runSimulation
  } = useQuantumStore();
  
  const handlePresetChange = (preset: string) => {
    setPresetCircuit(preset);
    if (preset in PRESET_CIRCUITS) {
      setQasmCode(PRESET_CIRCUITS[preset as keyof typeof PRESET_CIRCUITS].qasm);
    }
  };
  
  const handleRun = async () => {
    try {
      await runSimulation();
    } catch (error) {
      console.error('Simulation failed:', error);
      // Error handling is done in the store
    }
  };
  
  const handlePause = () => {
    setSimulationStatus('paused');
  };
  
  const handleStop = () => {
    resetSimulation();
  };
  
  // Validate QASM code
  const validateQasm = (code: string) => {
    const lines = code.split('\n').filter(line => line.trim());
    const hasHeader = lines.some(line => line.includes('OPENQASM'));
    const hasQreg = lines.some(line => line.includes('qreg'));
    const gateCount = lines.filter(line => 
      /^(h|x|y|z|cx|ry|rx|rz)\s/.test(line.trim())
    ).length;
    
    return { hasHeader, hasQreg, gateCount, isValid: hasHeader && hasQreg };
  };
  
  const validation = validateQasm(qasmCode);
  
  return (
    <Card className="quantum-card">
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-foreground">Quantum Circuit Editor</h2>
          <div className="flex items-center gap-2">
            <Badge variant={simulation.status === 'completed' ? 'default' : 'secondary'}>
              {simulation.pipeline.toUpperCase()}
            </Badge>
            <Badge variant={validation.isValid ? 'default' : 'destructive'}>
              {validation.isValid ? 'Valid' : 'Invalid'}
            </Badge>
          </div>
        </div>
        
        {/* Preset Circuits */}
        <div className="space-y-2">
          <Label htmlFor="preset">Circuit Presets</Label>
          <Select value={presetCircuit} onValueChange={handlePresetChange}>
            <SelectTrigger id="preset" className="bg-input border-border">
              <SelectValue placeholder="Select a preset circuit" />
            </SelectTrigger>
            <SelectContent className="bg-popover border-border">
              {Object.entries(PRESET_CIRCUITS).map(([key, circuit]) => (
                <SelectItem key={key} value={key} className="focus:bg-accent">
                  <div className="flex flex-col items-start">
                    <span className="font-medium">{circuit.name}</span>
                    <span className="text-xs text-muted-foreground">{circuit.description}</span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        
        {/* QASM Editor */}
        <div className="space-y-2">
          <Label htmlFor="qasm">OpenQASM 2.0 Code</Label>
          <Textarea
            id="qasm"
            value={qasmCode}
            onChange={(e) => setQasmCode(e.target.value)}
            className="min-h-[200px] font-mono text-sm bg-input border-border"
            placeholder="Enter your OpenQASM 2.0 code here..."
          />
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <InfoIcon className="w-3 h-3" />
              Gates: {validation.gateCount}
            </span>
            <span>Status: {validation.isValid ? 'Valid' : 'Invalid'}</span>
          </div>
        </div>
        
        {/* Simulation Controls */}
        <div className="flex gap-2 pt-4 border-t border-border">
          <Button 
            onClick={handleRun}
            disabled={!validation.isValid || simulation.status === 'running'}
            className="quantum-button flex-1"
          >
            <PlayIcon className="w-4 h-4 mr-2" />
            {simulation.status === 'running' ? 'Running...' : 'Run Simulation'}
          </Button>
          
          <Button 
            variant="outline" 
            onClick={handlePause}
            disabled={simulation.status !== 'running'}
            className="border-border hover:bg-accent"
          >
            <PauseIcon className="w-4 h-4" />
          </Button>
          
          <Button 
            variant="outline" 
            onClick={handleStop}
            disabled={simulation.status === 'idle'}
            className="border-border hover:bg-accent"
          >
            <SquareIcon className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </Card>
  );
};