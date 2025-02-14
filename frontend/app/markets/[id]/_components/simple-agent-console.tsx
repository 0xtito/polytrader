"use client";

/* <ai_context>
   This is a component that displays the streamed console output of the AI agent,
   along with optional controls for user confirmation to proceed with trades.
</ai_context> */

import React from "react";
import { AgentEvent } from "@/types/agent-stream-types";

interface StreamingAgentConsoleProps {
  streamOutput: string[];
  isStreaming: boolean;
  agentEvents: AgentEvent[];
  onTradeConfirmation: (decision: "YES" | "NO") => void;
}

export default function SimpleAgentConsole({
  // @ts-ignore
  streamOutput,
  isStreaming,
  agentEvents,
  onTradeConfirmation,
}: StreamingAgentConsoleProps) {
  return (
    <div className="rounded-xl border bg-card p-6 space-y-4 h-full">
      <h2 className="text-xl font-semibold">Agent Analysis</h2>

      <div className="h-64 overflow-auto bg-background border rounded p-2 text-sm">
        {agentEvents.map((event, idx) => (
          <div key={idx} className="mb-2">
            <strong>{event.name}:</strong>
            <pre className="whitespace-pre-wrap break-words">
              {JSON.stringify(event.data, null, 2)}
            </pre>
          </div>
        ))}
      </div>

      {isStreaming && (
        <div className="flex items-center text-sm text-muted-foreground">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary mr-2" />
          Streaming...
        </div>
      )}

      <div className="flex flex-wrap gap-4">
        <button
          className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
          onClick={() => onTradeConfirmation("YES")}
        >
          Confirm Trade
        </button>

        <button
          className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          onClick={() => onTradeConfirmation("NO")}
        >
          Deny Trade
        </button>
      </div>
    </div>
  );
}
