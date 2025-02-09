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
    <div className="p-2 bg-muted rounded">
      <span className="font-bold">Step {stepNumber}:</span> {message}
    </div>
  );
}