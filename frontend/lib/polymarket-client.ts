import { ClobClient } from "@polymarket/clob-client";
import { ethers } from "ethers";

let polyClient: ClobClient | null = null;

export function getPolymarketClient() {
  if (!polyClient) {
    if (!process.env.POLYMARKET_HOST) {
      throw new Error(
        "Missing required environment variables for Polymarket client"
      );
    }

    polyClient = new ClobClient(
      process.env.POLYMARKET_HOST,
      137 // Polygon chain ID
    );
  }

  return polyClient;
}

// Reset client (useful for testing)
export function resetPolymarketClient() {
  polyClient = null;
}
