"use server";

export interface Token {
  token_id: string;
  outcome: string;
}

interface Rewards {
  min_size: number;
  max_spread: number;
  event_start_date: string;
  event_end_date: string;
  in_game_multiplier: number;
  reward_epoch: number;
}

export interface Market {
  condition_id: string;
  question_id: string;
  tokens: [Token, Token];
  outcomePrices: string[];
  rewards: Rewards;
  minimum_order_size: string;
  minimum_tick_size: string;
  description: string;
  category: string;
  end_date: string;
  end_date_iso: string;
  game_start_time: string;
  question: string;
  market_slug: string;
  min_incentive_size: string;
  max_incentive_spread: string;
  active: boolean;
  closed: boolean;
  seconds_delay: number;
  icon: string;
  fpmm: string;
}

export interface Outcome {
  outcome: string;
  price: string;
}

export interface AdvancedMarket extends Market {
  outcomes: Outcome[];
  volume: string;
  volume24hrClob: number;
  volume24hrAmm: number;
  liquidity: string;
  liquidityClob: number;
  volumeClob: number;
  featured: boolean;
}

interface MarketsResponse {
  limit: number;
  count: number;
  next_cursor: string;
  data: Market[];
}

export async function getMarkets(
  nextCursor: string = ""
): Promise<MarketsResponse> {
  try {
    const response = await fetch(
      `https://clob.polymarket.com/markets?limit=10&next_cursor=${nextCursor}`
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data: MarketsResponse = await response.json();
    return data;
  } catch (error) {
    console.error("Error fetching markets:", error);
    throw error;
  }
}
