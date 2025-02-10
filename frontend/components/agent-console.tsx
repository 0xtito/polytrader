/* <ai_context>
   AgentConsole component streams real-time AI agent analysis output.
</ai_context> */
"use client";

import React, { useEffect, useState } from "react";
import AgentStep from "./agent-step";
import DecisionCard from "./decision-card";
import exampleRunData from "../data/example-run.json"; // Import the JSON file

interface AgentConsoleProps {
  marketId: number;
}

export default function AgentConsole({ marketId }: AgentConsoleProps) {
  const [steps, setSteps] = useState<string[]>([]);
  const [finalDecision, setFinalDecision] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // No need for try-catch with direct import, but we'll check the structure
    if (
      Array.isArray(exampleRunData) &&
      exampleRunData.length > 0 &&
      exampleRunData[0].values &&
      exampleRunData[0].values.external_research_info &&
      exampleRunData[0].values.external_research_info.research_summary
    ) {
      const researchSummary =
        exampleRunData[0].values.external_research_info.research_summary;
      setSteps(researchSummary.split(". ")); // Split into sentences
    } else {
      setError("Invalid JSON data structure.");
    }
  }, [marketId]);

  if (error) {
    return <div className="text-red-500">{error}</div>;
  }

  return (
    <div className="w-full rounded-lg bg-white shadow-lg p-6 dark:bg-gray-800">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">
          AI Agent Analysis
        </h2>
        <div className="flex items-center gap-2">
          <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
          <span className="text-sm text-gray-500 dark:text-gray-400">
            Live Analysis
          </span>
        </div>
      </div>

      {error ? (
        <div className="p-4 mb-4 text-sm rounded-lg bg-red-50 text-red-500 dark:bg-red-900/50 dark:text-red-200">
          <div className="flex items-center gap-2">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-5 w-5"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clipRule="evenodd"
              />
            </svg>
            {error}
          </div>
        </div>
      ) : (
        <>
          <div className="space-y-4 mb-6 max-h-[32rem] overflow-y-auto rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50 p-4 custom-scrollbar">
            {steps.map((step, index) => (
              <AgentStep key={index} stepNumber={index + 1} message={step} />
            ))}
          </div>

          {finalDecision && (
            <div className="mt-6">
              <DecisionCard decision={finalDecision} />
            </div>
          )}

          {steps.length === 0 && (
            <div className="flex flex-col items-center justify-center py-12 text-gray-500 dark:text-gray-400">
              <svg
                className="h-12 w-12 mb-4 animate-pulse"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                />
              </svg>
              <p className="text-lg font-medium">Initializing Analysis...</p>
              <p className="text-sm">
                Please wait while we process the market data
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
