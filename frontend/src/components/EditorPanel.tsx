import { Card } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useQuantumStore, PRESET_CIRCUITS } from '@/store/quantumStore';
import { PlayIcon, PauseIcon, SquareIcon, InfoIcon, Code2, Upload } from 'lucide-react';
import * as Tabs from '@radix-ui/react-tabs';
import { VisualEditor } from './editor/VisualEditor.tsx';
import { TransitionWrapper } from './TransitionWrapper.tsx';
import { QasmFileUploader } from './editor/QasmFileUploader.tsx';
import { MonacoQasmEditor } from './editor/MonacoQasmEditor.tsx';

export const EditorPanel = () => {
  const { 
    qasmCode, 
    setQasmCode, 
    presetCircuit, 
    setPresetCircuit,
    simulation,
    setSimulationStatus,
    resetSimulation,
    runSimulation,
    editorTab,
    setEditorTab,
    codeEditorMode,
    setCodeEditorMode,
    monacoEditorFullscreen,
    toggleMonacoFullscreen,
    uploadedFileName,
    loadFileContent
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

        {/* Presets */}
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

        {/* Tabs: Visual | Code */}
        <Tabs.Root value={editorTab} onValueChange={(v) => setEditorTab(v as 'visual'|'code')} className="w-full">
          <Tabs.List className="inline-flex h-10 items-center justify-center rounded-md bg-muted p-1 text-muted-foreground transition-all duration-300">
            <Tabs.Trigger 
              value="visual" 
              className="inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1 text-sm font-medium transition-all duration-300 data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm"
            >
              Visual
            </Tabs.Trigger>
            <Tabs.Trigger 
              value="code" 
              className="inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1 text-sm font-medium transition-all duration-300 data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm"
            >
              Code
            </Tabs.Trigger>
          </Tabs.List>

          <div className={`relative ${editorTab === 'code' && codeEditorMode === 'monaco' ? 'min-h-[600px]' : 'min-h-[400px]'} overflow-visible transition-all duration-500`}>
            <TransitionWrapper isActive={editorTab === 'visual'} direction="left" duration={500}>
              <div className={editorTab === 'visual' ? 'mt-4' : 'mt-4 absolute inset-0 pointer-events-none'}>
                <VisualEditor />
              </div>
            </TransitionWrapper>

            <TransitionWrapper isActive={editorTab === 'code'} direction="right" duration={500}>
              <div className={editorTab === 'code' ? 'mt-4 space-y-4' : 'mt-4 space-y-4 absolute inset-0 pointer-events-none'}>
                {/* Code Editor Mode Selection and File Upload */}
                <div className="p-3 bg-muted/30 rounded-lg border space-y-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <Button
                      variant={codeEditorMode === 'simple' ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setCodeEditorMode('simple')}
                      className="transition-all duration-200 flex-shrink-0"
                    >
                      Simple Editor
                    </Button>
                    <Button
                      variant={codeEditorMode === 'monaco' ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setCodeEditorMode('monaco')}
                      className="transition-all duration-200 flex-shrink-0"
                    >
                      <Code2 className="w-4 h-4 mr-1" />
                      Advanced Editor
                    </Button>
                    <QasmFileUploader onFileLoad={loadFileContent} />
                    {uploadedFileName && (
                      <Badge variant="secondary" className="text-xs flex-shrink-0 ml-1">
                        📄 {uploadedFileName}
                      </Badge>
                    )}
                  </div>
                </div>

                {/* Monaco Editor */}
                {codeEditorMode === 'monaco' && (
                  <div className="animate-in fade-in duration-500 w-full">
                    <MonacoQasmEditor
                      value={qasmCode}
                      onChange={setQasmCode}
                      isFullscreen={monacoEditorFullscreen}
                      onToggleFullscreen={toggleMonacoFullscreen}
                      onClose={() => setCodeEditorMode('simple')}
                    />
                  </div>
                )}

                {/* Simple Editor */}
                {codeEditorMode === 'simple' && (
                  <div className="space-y-2 animate-in fade-in duration-500">
                    <Label htmlFor="qasm">OpenQASM 2.0 Code</Label>
                    <Textarea
                      id="qasm"
                      value={qasmCode}
                      onChange={(e) => setQasmCode(e.target.value)}
                      className="min-h-[200px] font-mono text-sm bg-input border-border transition-all duration-300 focus:ring-2 focus:ring-quantum-primary/20"
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
                )}
              </div>
            </TransitionWrapper>
          </div>
        </Tabs.Root>

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