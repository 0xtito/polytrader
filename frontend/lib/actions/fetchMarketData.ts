"use server";

import { PolymarketData } from "@/types/market-types";

export async function fetchMarketData(
  marketId: string
): Promise<PolymarketData> {
  try {
    const response = await fetch(
      `https://clob.polymarket.com/markets/${marketId}`
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data as PolymarketData;
  } catch (error) {
    console.error("Error fetching market data:", error);
    throw error;
  }
}
