import React, { ReactNode } from 'react';

interface TransitionWrapperProps {
  children: ReactNode;
  isActive: boolean;
  className?: string;
  direction?: 'left' | 'right' | 'up' | 'down';
  duration?: number;
}

export const TransitionWrapper: React.FC<TransitionWrapperProps> = ({
  children,
  isActive,
  className = '',
  direction = 'right',
  duration = 500
}) => {
  const getTransformClass = () => {
    if (!isActive) {
      switch (direction) {
        case 'left': return '-translate-x-8 opacity-0';
        case 'right': return 'translate-x-8 opacity-0';
        case 'up': return '-translate-y-8 opacity-0';
        case 'down': return 'translate-y-8 opacity-0';
        default: return 'translate-x-8 opacity-0';
      }
    }
    return 'translate-x-0 translate-y-0 opacity-100';
  };

  const durationClass = duration === 300 ? 'duration-300' : 
                       duration === 500 ? 'duration-500' : 
                       duration === 700 ? 'duration-700' : 'duration-500';

  return (
    <div 
      className={`transition-all ${durationClass} ease-in-out transform ${getTransformClass()} ${className}`}
      style={{ transitionDelay: isActive ? '0ms' : '50ms' }}
    >
      {children}
    </div>
  );
};

export default TransitionWrapper;
