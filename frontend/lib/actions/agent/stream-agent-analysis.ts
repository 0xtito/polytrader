"use server";

import { Client, type Config } from "@langchain/langgraph-sdk";
import { Token } from "../polymarket/getMarkets";

const DEPLOYMENT_URL = process.env.LANGGRAPH_DEPLOYMENT_URL;
const ASSISTANT_ID = "polytrader";

export async function streamAgentAnalysis(marketId: number, tokens: Token[]) {
  try {
    console.log("DEPLOYMENT_URL", DEPLOYMENT_URL);
    const client = new Client({ apiUrl: DEPLOYMENT_URL! });

    console.log("client", client);

    const thread = await client.threads.create();

    const input = {
      market_id: marketId.toString(),
      from_js: true,
      tokens: tokens,
    };

    const config: Config = {
      configurable: {
        thread_id: thread.thread_id,
      },
    };

    return {
      stream: client.runs.stream(thread.thread_id, ASSISTANT_ID, {
        input,
        streamMode: "updates",
        interruptBefore: ["human_confirmation_js"],
      }),
      config,
    };
  } catch (error) {
    console.error("Error in streamAgentAnalysis:", error);
    throw error;
  }
}

// export async function writeStreamToFile(streamData: any) {
//   const date = new Date().toISOString().split("T")[0];
//   const fs = require("fs");
//   const path = require("path");

//   // Create data directory if it doesn't exist
//   const dataDir = path.join(process.cwd(), "data");
//   if (!fs.existsSync(dataDir)) {
//     fs.mkdirSync(dataDir, { recursive: true });
//   }

//   const filename = path.join(dataDir, `stream_${date}.json`);
//   fs.writeFileSync(filename, JSON.stringify(streamData, null, 2));
// }
