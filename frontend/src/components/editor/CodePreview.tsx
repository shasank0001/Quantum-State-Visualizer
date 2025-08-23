import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Copy, Code2, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';
import { useQuantumStore } from '@/store/quantumStore';
import { useToast } from '@/hooks/use-toast';

export const CodePreview: React.FC = () => {
  const { 
    qasmCode, 
    qasmValidation, 
    visualValidation,
    compileVisualToQASM, 
    validateQASM, 
    validateVisualCircuit 
  } = useQuantumStore();
  const { toast } = useToast();
  const [isCompiling, setIsCompiling] = useState(false);

  // Auto-compile when visual circuit changes
  useEffect(() => {
    const timer = setTimeout(() => {
      setIsCompiling(true);
      try {
        compileVisualToQASM();
        validateVisualCircuit();
      } catch (error) {
        console.error('Auto-compilation error:', error);
      } finally {
        setIsCompiling(false);
      }
    }, 300); // Debounce compilation

    return () => clearTimeout(timer);
  }, [compileVisualToQASM, validateVisualCircuit]);

  const handleCopyCode = async () => {
    try {
      await navigator.clipboard.writeText(qasmCode || '');
      toast({
        description: "OpenQASM code copied to clipboard",
        duration: 2000,
      });
    } catch (error) {
      console.error('Failed to copy code:', error);
      toast({
        title: "Copy failed",
        description: "Could not copy code to clipboard",
        variant: "destructive",
        duration: 3000,
      });
    }
  };

  const handleManualCompile = () => {
    setIsCompiling(true);
    try {
      compileVisualToQASM();
      validateVisualCircuit();
      toast({
        description: "Circuit compiled successfully",
        duration: 2000,
      });
    } catch (error) {
      console.error('Manual compilation error:', error);
      toast({
        title: "Compilation failed",
        description: "Failed to compile visual circuit",
        variant: "destructive",
        duration: 3000,
      });
    } finally {
      setIsCompiling(false);
    }
  };

  const getValidationStatus = () => {
    const visualErrors = visualValidation?.errors?.length || 0;
    const qasmErrors = qasmValidation?.errors?.length || 0;
    const totalErrors = visualErrors + qasmErrors;
    
    const visualWarnings = visualValidation?.warnings?.length || 0;
    const qasmWarnings = qasmValidation?.warnings?.length || 0;
    const totalWarnings = visualWarnings + qasmWarnings;

    if (totalErrors > 0) {
      return { status: 'error', count: totalErrors, icon: XCircle, color: 'destructive' };
    }
    if (totalWarnings > 0) {
      return { status: 'warning', count: totalWarnings, icon: AlertTriangle, color: 'secondary' };
    }
    return { status: 'valid', count: 0, icon: CheckCircle, color: 'default' };
  };

  const validationStatus = getValidationStatus();
  const StatusIcon = validationStatus.icon;

  return (
    <Card className="h-full flex flex-col animate-in fade-in duration-500">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Code2 className="h-5 w-5 transition-transform duration-300 hover:scale-110" />
              OpenQASM 2.0 Preview
            </CardTitle>
            <CardDescription>
              Generated circuit code for the visual editor
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Badge 
              variant={validationStatus.color as any}
              className="flex items-center gap-1 transition-all duration-300"
            >
              <StatusIcon className="h-3 w-3 transition-all duration-300" />
              {validationStatus.status === 'valid' ? 'Valid' : 
               validationStatus.status === 'warning' ? `${validationStatus.count} Warning${validationStatus.count > 1 ? 's' : ''}` :
               `${validationStatus.count} Error${validationStatus.count > 1 ? 's' : ''}`}
            </Badge>
            <Button
              variant="outline"
              size="sm"
              onClick={handleManualCompile}
              disabled={isCompiling}
              className="transition-all duration-200 hover:scale-105"
            >
              {isCompiling ? 'Compiling...' : 'Refresh'}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleCopyCode}
              disabled={!qasmCode}
              className="transition-all duration-200 hover:scale-105"
            >
              <Copy className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="flex-1 flex flex-col gap-4">
        {/* Code Display */}
        <div className="flex-1 relative">
          <pre className="bg-muted/50 rounded-md p-4 text-sm font-mono overflow-auto h-full min-h-[200px] border transition-all duration-300 hover:bg-muted/70">
            <code className="text-foreground transition-all duration-300">
              {qasmCode || '// No circuit defined yet\n// Add gates to the visual editor above'}
            </code>
          </pre>
          {isCompiling && (
            <div className="absolute inset-0 bg-background/50 flex items-center justify-center rounded-md transition-all duration-300">
              <div className="flex items-center gap-2 bg-background border rounded-lg px-3 py-2 animate-in zoom-in duration-200">
                <div className="animate-spin h-4 w-4 border-2 border-primary border-t-transparent rounded-full" />
                <span className="text-sm">Compiling...</span>
              </div>
            </div>
          )}
        </div>

        {/* Validation Messages */}
        {(visualValidation?.errors?.length || qasmValidation?.errors?.length || 
          visualValidation?.warnings?.length || qasmValidation?.warnings?.length) && (
          <div className="space-y-2 animate-in slide-in-from-bottom duration-400">
            {/* Visual Circuit Errors */}
            {visualValidation?.errors?.map((error, idx) => (
              <div key={`visual-error-${idx}`} className="flex items-start gap-2 p-2 bg-destructive/10 border border-destructive/20 rounded text-sm animate-in slide-in-from-left duration-300" style={{animationDelay: `${idx * 100}ms`}}>
                <XCircle className="h-4 w-4 text-destructive mt-0.5 flex-shrink-0" />
                <div>
                  <span className="font-medium text-destructive">Visual Circuit:</span>
                  <span className="ml-2 text-foreground">{error}</span>
                </div>
              </div>
            ))}

            {/* QASM Errors */}
            {qasmValidation?.errors?.map((error, idx) => (
              <div key={`qasm-error-${idx}`} className="flex items-start gap-2 p-2 bg-destructive/10 border border-destructive/20 rounded text-sm animate-in slide-in-from-left duration-300" style={{animationDelay: `${idx * 100}ms`}}>
                <XCircle className="h-4 w-4 text-destructive mt-0.5 flex-shrink-0" />
                <div>
                  <span className="font-medium text-destructive">Generated Code:</span>
                  <span className="ml-2 text-foreground">{error}</span>
                </div>
              </div>
            ))}

            {/* Visual Circuit Warnings */}
            {visualValidation?.warnings?.map((warning, idx) => (
              <div key={`visual-warning-${idx}`} className="flex items-start gap-2 p-2 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded text-sm animate-in slide-in-from-left duration-300" style={{animationDelay: `${idx * 100}ms`}}>
                <AlertTriangle className="h-4 w-4 text-yellow-600 dark:text-yellow-400 mt-0.5 flex-shrink-0" />
                <div>
                  <span className="font-medium text-yellow-800 dark:text-yellow-200">Visual Circuit:</span>
                  <span className="ml-2 text-foreground">{warning}</span>
                </div>
              </div>
            ))}

            {/* QASM Warnings */}
            {qasmValidation?.warnings?.map((warning, idx) => (
              <div key={`qasm-warning-${idx}`} className="flex items-start gap-2 p-2 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded text-sm animate-in slide-in-from-left duration-300" style={{animationDelay: `${idx * 100}ms`}}>
                <AlertTriangle className="h-4 w-4 text-yellow-600 dark:text-yellow-400 mt-0.5 flex-shrink-0" />
                <div>
                  <span className="font-medium text-yellow-800 dark:text-yellow-200">Generated Code:</span>
                  <span className="ml-2 text-foreground">{warning}</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Success Message */}
        {validationStatus.status === 'valid' && qasmCode && (
          <div className="flex items-center gap-2 p-2 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded text-sm animate-in slide-in-from-bottom duration-300">
            <CheckCircle className="h-4 w-4 text-green-600 dark:text-green-400 flex-shrink-0" />
            <span className="text-green-800 dark:text-green-200">Circuit is valid and ready for simulation</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default CodePreview;
