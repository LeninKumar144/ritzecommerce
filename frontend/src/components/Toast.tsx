import { createContext, useContext, useState, type ReactNode } from "react";

type ToastContextValue = {
  message: string | null;
  notify: (message: string) => void;
};

const ToastContext = createContext<ToastContextValue>({ message: null, notify: () => undefined });

export function ToastProvider({ children }: { children: ReactNode }) {
  const [message, setMessage] = useState<string | null>(null);

  function notify(next: string) {
    setMessage(next);
    window.setTimeout(() => setMessage(null), 3200);
  }

  return (
    <ToastContext.Provider value={{ message, notify }}>
      {children}
      {message ? (
        <div
          role="status"
          className="fixed right-4 bottom-4 z-50 max-w-sm rounded-2xl bg-ink px-4 py-3 text-sm text-paper shadow-lg"
        >
          {message}
        </div>
      ) : null}
    </ToastContext.Provider>
  );
}

export function useToast() {
  return useContext(ToastContext);
}
