import { useState, useCallback, createContext, useContext, type ReactNode } from 'react';
import { Icon } from './ui/Icon';

export interface Toast {
  id: string;
  message: string;
  type: 'success' | 'error' | 'info';
  duration?: number;
}

interface ToastContextType {
  toasts: Toast[];
  addToast: (message: string, type: Toast['type'], duration?: number) => void;
  removeToast: (id: string) => void;
}

export const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const addToast = useCallback(
    (message: string, type: Toast['type'], duration = 3000) => {
      const id = Math.random().toString(36).substring(7);
      setToasts((prev) => [...prev, { id, message, type, duration }]);
      if (duration > 0) {
        setTimeout(() => removeToast(id), duration);
      }
    },
    [removeToast]
  );

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast }}>
      {children}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) throw new Error('useToast must be used within ToastProvider');
  return context;
}

function ToastContainer({ toasts, onRemove }: { toasts: Toast[]; onRemove: (id: string) => void }) {
  return (
    <div className="fixed bottom-20 md:bottom-4 right-4 space-y-2 z-[100] max-w-sm">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onRemove={onRemove} />
      ))}
    </div>
  );
}

function ToastItem({ toast, onRemove }: { toast: Toast; onRemove: (id: string) => void }) {
  const [isExiting, setIsExiting] = useState(false);

  const styles = {
    success: 'bg-surface-container-high border-primary/40 text-on-surface',
    error: 'bg-error-container/30 border-error/50 text-error',
    info: 'bg-surface-container border-outline-variant text-on-surface',
  }[toast.type];

  const icon = { success: 'check_circle', error: 'error', info: 'info' }[toast.type];

  return (
    <div
      className={`${styles} border px-4 py-3 rounded-btn text-body-sm flex items-center gap-3 shadow-elevated transition-all ${
        isExiting ? 'opacity-0 translate-y-1' : 'opacity-100'
      }`}
    >
      <Icon name={icon} size={20} />
      <span className="flex-1">{toast.message}</span>
      <button
        type="button"
        onClick={() => {
          setIsExiting(true);
          setTimeout(() => onRemove(toast.id), 200);
        }}
        className="text-on-surface-variant hover:text-on-surface"
      >
        <Icon name="close" size={18} />
      </button>
    </div>
  );
}
