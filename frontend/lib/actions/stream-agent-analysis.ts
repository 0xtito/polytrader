"use server";

import { Client } from "@langchain/langgraph-sdk";

const DEPLOYMENT_URL = process.env.LANGGRAPH_DEPLOYMENT_URL;
const ASSISTANT_ID = "polytrader";

export async function streamAgentAnalysis(marketId: number) {
  try {
    console.log("DEPLOYMENT_URL", DEPLOYMENT_URL);
    const client = new Client({ apiUrl: DEPLOYMENT_URL! });

    console.log("client", client);

    const thread = await client.threads.create();

    const input = {
      market_id: marketId.toString(),
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
      streamMode: "updates",
    });
  } catch (error) {
    console.error("Error in streamAgentAnalysis:", error);
    throw error;
  }
}

export async function writeStreamToFile(streamData: any) {
  const date = new Date().toISOString().split("T")[0];
  const fs = require("fs");
  const path = require("path");

  // Create data directory if it doesn't exist
  const dataDir = path.join(process.cwd(), "data");
  if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true });
  }

  const filename = path.join(dataDir, `stream_${date}.json`);
  fs.writeFileSync(filename, JSON.stringify(streamData, null, 2));
}
