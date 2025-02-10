"use server";

import { Client } from "@langchain/langgraph-sdk";

// This would come from your environment variables
const DEPLOYMENT_URL = process.env.LANGGRAPH_DEPLOYMENT_URL;
const ASSISTANT_ID = "agent";

export async function streamAgentAnalysis(marketId: number) {
  try {
    const client = new Client({ apiUrl: DEPLOYMENT_URL! });

    // Create thread
    const thread = await client.threads.create();

    // Prepare input with market_id
    const input = {
      market_id: marketId,
      custom_instructions: null,
      extraction_schema: {
        headline: "",
        summary: "",
        source_links: [],
      },
    };

    // Return the stream
    return client.runs.stream(thread.thread_id, ASSISTANT_ID, {
      input,
      streamMode: "values",
    });
  } catch (error) {
    console.error("Error in streamAgentAnalysis:", error);
    throw error;
  }
}
