import React, { createContext, useContext, useState, useCallback } from 'react';

interface ToastContextType {
  success: (message: string) => void;
  error: (message: string) => void;
  info: (message: string) => void;
  warning: (message: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<{ id: number; message: string; type: string }[]>([]);

  const addToast = useCallback((message: string, type: string) => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((toast) => toast.id !== id));
    }, 3000);
  }, []);

  const success = useCallback((message: string) => addToast(message, 'success'), [addToast]);
  const error = useCallback((message: string) => addToast(message, 'error'), [addToast]);
  const info = useCallback((message: string) => addToast(message, 'info'), [addToast]);
  const warning = useCallback((message: string) => addToast(message, 'warning'), [addToast]);

  return (
    <ToastContext.Provider value={{ success, error, info, warning }}>
      {children}
      <div style={{ position: 'fixed', bottom: 20, right: 20, zIndex: 9999 }}>
        {toasts.map((toast) => (
          <div
            key={toast.id}
            style={{
              background: toast.type === 'error' ? '#fee2e2' : toast.type === 'success' ? '#dcfce7' : '#fff',
              color: toast.type === 'error' ? '#991b1b' : toast.type === 'success' ? '#166534' : '#333',
              padding: '10px 20px',
              margin: '5px',
              borderRadius: '4px',
              boxShadow: '0 2px 5px rgba(0,0,0,0.2)',
            }}
          >
            {toast.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = () => {
  const context = useContext(ToastContext);
  if (context === undefined) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};
