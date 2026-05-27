import React from 'react';

interface HealthCheckProps {
  isHealthy: boolean;
}

export function HealthCheck({ isHealthy }: HealthCheckProps) {
  return (
    <footer className="border-t border-sage-200 bg-white px-8 py-3 text-xs">
      <div className="flex items-center gap-2">
        <div className={`w-2 h-2 rounded-full ${isHealthy ? 'bg-sage-600' : 'bg-red-500'}`}></div>
        <span className={`transition-all duration-300 ${isHealthy ? 'text-sage-600' : 'text-red-600'}`}>
          {isHealthy ? 'Backend connected' : 'Backend disconnected'}
        </span>
      </div>
    </footer>
  );
}
