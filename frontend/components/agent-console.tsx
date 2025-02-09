/* <ai_context>
   AgentConsole component streams real-time AI agent analysis output.
</ai_context> */
"use client";

import React, { useEffect, useState } from "react";
import AgentStep from "./agent-step";
import DecisionCard from "./decision-card";

interface AgentConsoleProps {
  marketId: number;
}

export default function AgentConsole({ marketId }: AgentConsoleProps) {
  const [steps, setSteps] = useState<string[]>([]);
  const [finalDecision, setFinalDecision] = useState<string | null>(null);

  useEffect(() => {
    // Simulate WebSocket streaming with timeouts
    const simulatedSteps = [
      "Connecting to AI agent...",
      "Fetching market data...",
      "Analyzing recent price trends...",
      "Assessing news sentiment...",
      "Computing optimal trading position..."
    ];
    simulatedSteps.forEach((step, index) => {
      setTimeout(() => {
        setSteps(prev => [...prev, step]);
      }, (index + 1) * 1000);
    });
    setTimeout(() => {
      setFinalDecision("BUY");
      setSteps(prev => [...prev, "Final recommendation received."]);
    }, (simulatedSteps.length + 1) * 1000);
  }, [marketId]);

  return (
    <div>
      <h2 className="text-xl font-bold mb-2">AI Agent Analysis</h2>
      <div className="space-y-2 max-h-64 overflow-y-auto border p-2 rounded">
        {steps.map((step, index) => (
          <AgentStep key={index} stepNumber={index + 1} message={step} />
        ))}
      </div>
      {finalDecision && <DecisionCard decision={finalDecision} />}
    </div>
  );
}