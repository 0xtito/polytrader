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
