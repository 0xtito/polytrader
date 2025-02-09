/* <ai_context>
   AgentStep component displays a single step from the AI agent.
</ai_context> */
"use client";

import React from "react";

interface AgentStepProps {
  stepNumber: number;
  message: string;
}

export default function AgentStep({ stepNumber, message }: AgentStepProps) {
  return (
    <div className="flex items-start gap-3 p-4 rounded-lg bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
      <div className="flex-shrink-0">
        <div className="w-6 h-6 rounded-full bg-primary/10 dark:bg-primary/20 flex items-center justify-center">
          <span className="text-xs font-medium text-primary dark:text-primary-foreground">
            {stepNumber}
          </span>
        </div>
      </div>

      <div className="flex-1 min-w-0">
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          {message}
        </p>
      </div>
    </div>
  );
}
