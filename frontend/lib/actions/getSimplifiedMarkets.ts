"use server";

interface Token {
  token_id: string;
  token_address: string;
  token_name: string;
  token_symbol: string;
}

interface Rewards {
  asset_address: string;
  rewards_amount: string;
  rewards_daily_rate: string;
  start_date: string;
  end_date: string;
}

interface SimplifiedMarket {
  condition_id: string;
  tokens: [Token, Token];
  rewards: Rewards;
  min_incentive_size: string;
  max_incentive_spread: string;
  active: boolean;
  closed: boolean;
}

interface SimplifiedMarketsResponse {
  limit: number;
  count: number;
  next_cursor: string;
  data: SimplifiedMarket[];
}

export async function getSimplifiedMarkets(nextCursor: string = "") {
  try {
    const response = await fetch(
      `https://clob.polymarket.com/simplified-markets?next_cursor=${nextCursor}`
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data: SimplifiedMarketsResponse = await response.json();
    return data;
  } catch (error) {
    console.error("Error fetching simplified markets:", error);
    throw error;
  }
}

// Export types for use in other files
export type { SimplifiedMarket, SimplifiedMarketsResponse };
