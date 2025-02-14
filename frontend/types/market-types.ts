import { Token } from "@/lib/actions/polymarket/getMarkets";

interface ClobReward {
  id: string;
  conditionId: string;
  assetAddress: string;
  rewardsAmount: number;
  rewardsDailyRate: number;
  startDate: string;
  endDate: string;
}

export interface PolymarketData {
  enable_order_book: boolean;
  active: boolean;
  closed: boolean;
  archived: boolean;
  accepting_orders: boolean;
  accepting_order_timestamp: string | null;
  minimum_order_size: number;
  minimum_tick_size: number;
  condition_id: string;
  question_id: string;
  question: string;
  description: string;
  market_slug: string;
  end_date_iso: string;
  game_start_time: string;
  seconds_delay: number;
  fpmm: string;
  maker_base_fee: number;
  taker_base_fee: number;
  notifications_enabled: boolean;
  neg_risk: boolean;
  neg_risk_market_id: string;
  neg_risk_request_id: string;
  icon: string;
  image: string;
  rewards: {
    rates: null | any;
    min_size: number;
    max_spread: number;
  };
  is_50_50_outcome: boolean;
  tokens: Token[];
  tags: string[];
  volume24hr?: number;
  volumeNum?: number;
  liquidityNum?: number;
  oneDayPriceChange?: number;
  lastTradePrice?: number;
  bestBid?: number;
  bestAsk?: number;
  spread?: number;
}

// Helper type for parsed outcomes
export interface ParsedMarketData extends PolymarketData {
  parsedOutcomes: string[];
  parsedPrices: number[];
  parsedClobTokenIds: string[];
}
