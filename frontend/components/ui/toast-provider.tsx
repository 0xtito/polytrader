/* <ai_context>
   A ToastProvider for shadcn style toast with minimal state management.
</ai_context> */
"use client";

import React, { useState } from "react";
import { Toast, ToastProps } from "./toast";
import { ToastContext } from "./use-toast";
import { nanoid } from "nanoid";

export default function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastProps[]>([]);

  function addToast(toast: Omit<ToastProps, "id">) {
    setToasts((prev) => [...prev, { ...toast, id: nanoid() }]);
  }

  function removeToast(id: string) {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }

  return (
    <ToastContext.Provider value={{ addToast, removeToast }}>
      {children}

      <div className="fixed top-4 right-4 z-50 space-y-2">
        {toasts.map((toast) => (
          <Toast key={toast.id} {...toast} />
        ))}
      </div>
    </ToastContext.Provider>
  );
}