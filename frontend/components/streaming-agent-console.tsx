"use client";

import React, { useEffect, useState } from "react";
import { streamAgentAnalysis } from "@/lib/actions/stream-agent-analysis";

interface StreamingAgentConsoleProps {
  marketId: number;
}

export default function StreamingAgentConsole({
  marketId,
}: StreamingAgentConsoleProps) {
  const [streamOutput, setStreamOutput] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);

  useEffect(() => {
    const startStream = async () => {
      try {
        setIsStreaming(true);
        const stream = await streamAgentAnalysis(marketId);

        for await (const chunk of stream) {
          setStreamOutput((prev) => [
            ...prev,
            `Event Type: ${chunk.event}`,
            `Data: ${JSON.stringify(chunk.data, null, 2)}`,
            "---",
          ]);
        }
      } catch (err) {
        console.error("Streaming error:", err);
        setError(
          err instanceof Error
            ? err.message
            : "An error occurred while streaming"
        );
      } finally {
        setIsStreaming(false);
      }
    };

    startStream();
  }, [marketId]);

  if (error) {
    return <div className="text-red-500">{error}</div>;
  }

  return (
    <div className="w-full rounded-lg bg-white shadow-lg p-6 dark:bg-gray-800">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">
          AI Agent Analysis (Streaming)
        </h2>
        {isStreaming && (
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
            <span className="text-sm text-gray-500 dark:text-gray-400">
              Streaming...
            </span>
          </div>
        )}
      </div>

      <div className="space-y-4 mb-6 max-h-[32rem] overflow-y-auto rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50 p-4 custom-scrollbar font-mono text-sm">
        {streamOutput.map((output, index) => (
          <pre key={index} className="whitespace-pre-wrap">
            {output}
          </pre>
        ))}

        {streamOutput.length === 0 && isStreaming && (
          <div className="flex flex-col items-center justify-center py-12 text-gray-500 dark:text-gray-400">
            <div className="h-8 w-8 border-4 border-t-transparent border-primary rounded-full animate-spin mb-4" />
            <p>Initializing stream...</p>
          </div>
        )}
      </div>
    </div>
  );
}
