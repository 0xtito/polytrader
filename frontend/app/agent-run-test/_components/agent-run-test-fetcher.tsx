"use client";

import React from "react";
import type { AgentRunData } from "@/types/agent-run-types";

/* <ai_context>
   Client component that parses a hardcoded JSON snippet and displays
   some fields using the AgentRunData interface.
</ai_context> */

export default function AgentRunTestFetcher() {
  // Example JSON snippet from the user's agentic system
  const rawJson = `{
    "messages": [
      {
        "content": "",
        "additional_kwargs": {},
        "response_metadata": {},
        "type": "ai",
        "name": null,
        "id": "run-5cc93588-65c5-4000-a593-7594b79546df",
        "example": false,
        "tool_calls": [],
        "invalid_tool_calls": [],
        "usage_metadata": null
      }
    ],
    "trade_info": {
      "side": "SELL",
      "reason": "Market analysis and external research indicate that while the Eagles have potential, they are currently seen as slight underdogs in a highly competitive environment. The market pricing (~47.4% probability for a ‘Yes’ outcome) along with expert commentary suggests that the odds for an Eagles win may be slightly overestimated. Furthermore, the market’s efficient pricing—characterized by a narrow bid/ask spread, high liquidity, and significant trading volume—supports the view that there’s minimal upward momentum toward a more favorable 'Yes' outcome. Given these factors, I am taking a sell position.",
      "confidence": 0.85
    },
    "loop_step": 9
  }`;

  const parsedData: AgentRunData = JSON.parse(rawJson);

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-2xl font-bold">Agent Run Data Demo</h1>

      <div className="border p-2 rounded space-y-2">
        <p>
          <strong>Number of messages:</strong> {parsedData.messages.length}
        </p>

        {parsedData.trade_info && (
          <>
            <p>
              <strong>Trade Side:</strong> {parsedData.trade_info.side}
            </p>
            <p>
              <strong>Reason:</strong> {parsedData.trade_info.reason}
            </p>
            <p>
              <strong>Confidence:</strong> {parsedData.trade_info.confidence}
            </p>
          </>
        )}

        <p>
          <strong>Loop Step:</strong>{" "}
          {typeof parsedData.loop_step === "number"
            ? parsedData.loop_step
            : "N/A"}
        </p>
      </div>
    </div>
  );
}