"use server";

import { Suspense } from "react";
import AgentRunTestFetcher from "./_components/agent-run-test-fetcher";

/**
 * Server component to demonstrate usage of the AgentRunData interface
 * and display parsed data from the example JSON snippet.
 */
export default async function AgentRunTestPage() {
  return (
    <Suspense fallback={<div>Loading data...</div>}>
      <AgentRunTestFetcher />
    </Suspense>
  );
}