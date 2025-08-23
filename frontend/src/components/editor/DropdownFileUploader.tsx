import React, { useRef } from 'react';
import { Upload } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface DropdownFileUploaderProps {
  onFileLoad: (content: string, filename: string) => void;
  onUploadClick?: () => void;
}

export const DropdownFileUploader: React.FC<DropdownFileUploaderProps> = ({ 
  onFileLoad, 
  onUploadClick 
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file extension
    if (!file.name.toLowerCase().endsWith('.qasm') && !file.name.toLowerCase().endsWith('.txt')) {
      toast({
        title: "Invalid file type",
        description: "Please upload a .qasm or .txt file containing OpenQASM code",
        variant: "destructive",
        duration: 3000,
      });
      return;
    }

    // Validate file size (max 1MB)
    if (file.size > 1024 * 1024) {
      toast({
        title: "File too large",
        description: "Please upload a file smaller than 1MB",
        variant: "destructive",
        duration: 3000,
      });
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const content = e.target?.result as string;
        if (content) {
          onFileLoad(content, file.name);
          toast({
            title: "File uploaded successfully",
            description: `Loaded ${file.name}`,
            duration: 2000,
          });
        }
      } catch (error) {
        console.error('Error reading file:', error);
        toast({
          title: "Error reading file",
          description: "Could not read the selected file",
          variant: "destructive",
          duration: 3000,
        });
      }
    };

    reader.onerror = () => {
      toast({
        title: "Error reading file",
        description: "Could not read the selected file",
        variant: "destructive",
        duration: 3000,
      });
    };

    reader.readAsText(file);
    
    // Reset the input value to allow uploading the same file again
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleClick = () => {
    onUploadClick?.();
    fileInputRef.current?.click();
  };

  return (
    <>
      <input
        ref={fileInputRef}
        type="file"
        accept=".qasm,.txt"
        onChange={handleFileUpload}
        className="hidden"
        aria-label="Upload QASM file"
      />
      <div 
        onClick={handleClick}
        className="flex items-center gap-2 cursor-pointer"
      >
        <Upload className="w-4 h-4" />
        <span>Upload .qasm file</span>
      </div>
    </>
  );
};

export default DropdownFileUploader;
