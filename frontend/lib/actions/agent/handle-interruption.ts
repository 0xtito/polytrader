"use server";

import { Client, Command, Config } from "@langchain/langgraph-sdk";

const DEPLOYMENT_URL = process.env.LANGGRAPH_DEPLOYMENT_URL;
const ASSISTANT_ID = "polytrader";

export async function handleInterrupt(decision: "YES" | "NO", config: Config) {
  try {
    console.log("DEPLOYMENT_URL", DEPLOYMENT_URL);
    const client = new Client({ apiUrl: DEPLOYMENT_URL! });

    console.log("client", client);

    const threadId = config.configurable.thread_id;

    if (!threadId) {
      throw new Error("Thread ID is required");
    }

    let t = await client.threads.updateState(threadId, {
      values: {
        user_confirmation: decision === "YES",
      },
    });

    console.log("t", t);

    return client.runs.stream(threadId, ASSISTANT_ID, {
      input: null,
      streamMode: "updates",
      multitaskStrategy: "interrupt",
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
