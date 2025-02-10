/* <ai_context>
   This file exports a useToast hook from Shadcn UI system. 
   If you already have a toast provider, you can adapt or skip.
</ai_context> */
"use client";

import { createContext, useContext } from "react";
import { ToastActionElement, type ToastProps } from "./toast";

export interface ToastContextValue {
  addToast: (toast: ToastProps) => void;
  removeToast: (id: string) => void;
}

export const ToastContext = createContext<ToastContextValue | undefined>(
  undefined
);

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    throw new Error("useToast must be used within a ToastProvider");
  }

  return {
    toast: ({
      title,
      description,
      action,
      ...props
    }: {
      title?: string;
      description?: string;
      action?: ToastActionElement;
    } & Omit<ToastProps, "id">) => {
      ctx.addToast({
        title,
        description,
        action,
        ...props
      });
    }
  };
}