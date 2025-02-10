"use server";

export interface RawGammaMarket {
  id: string;
  question: string;
  conditionId: string;
  slug: string;
  resolutionSource: string;
  endDate: string;
  startDate: string;
  image: string;
  icon: string;
  description: string;
  outcomes: string; // This is a JSON string
  outcomePrices: string; // This is a JSON string
  volume: string;
  liquidity: string;
  active: boolean;
  closed: boolean;
  marketMakerAddress: string;
  createdAt: string;
  updatedAt: string;
  new: boolean;
  featured: boolean;
  submitted_by: string;
  archived: boolean;
  restricted: boolean;
  groupItemTitle: string;
  groupItemThreshold: string;
  enableOrderBook: boolean;
  orderPriceMinTickSize: number;
  orderMinSize: number;
  startDateIso: string;
  volume24hrAmm: number;
  volume24hrClob: number;
  volumeAmm: number;
  volumeClob: number;
  liquidityAmm: number;
  liquidityClob: number;
  negRisk: boolean;
  spread: number;
  oneDayPriceChange: number;
  lastTradePrice: number;
  bestBid: number;
  bestAsk: number;
  clobTokenIds: string; // This is a JSON string
}

export interface GammaMarket
  extends Omit<RawGammaMarket, "outcomes" | "clobTokenIds" | "outcomePrices"> {
  outcomes: string[];
  clobTokenIds: string[];
  outcomePrices: string[];
  volumeNum: number; // Computed from volumeAmm + volumeClob
  liquidityNum: number; // Computed from liquidityAmm + liquidityClob
  title: string; // Same as question
  endDate: string; // Same as endDate
  startDate: string; // Same as startDate
  imageUrl: string; // Same as image
  category: string; // We can default this to "General" or extract from groupItemTitle
  subcategory: string; // Can be empty string
  status: string; // Computed from active/closed
}

interface GammaMarketsResponse {
  markets: GammaMarket[];
}

function safeJsonParse<T>(
  jsonString: string | null | undefined,
  defaultValue: T
): T {
  if (!jsonString) return defaultValue;
  try {
    return JSON.parse(jsonString) as T;
  } catch (error) {
    console.warn("Failed to parse JSON string:", error);
    return defaultValue;
  }
}

export async function getGammaMarkets(
  limit: number = 10,
  offset: number = 0,
  options?: {
    marketId?: string;
    order?: string;
    ascending?: boolean;
    archived?: boolean;
    active?: boolean;
    closed?: boolean;
    liquidityNumMin?: number;
    volumeNumMin?: number;
    startDateMin?: string;
    endDateMin?: string;
  }
): Promise<GammaMarketsResponse> {
  const params = new URLSearchParams({
    limit: limit.toString(),
    offset: offset.toString(),
  });

  // Add optional parameters if they exist
  if (options) {
    if (options.marketId) params.append("id", options.marketId);
    if (options.order) {
      params.append("order", options.order);
      if (options.ascending !== undefined) {
        params.append("ascending", options.ascending.toString());
      }
    }
    if (options.archived !== undefined)
      params.append("archived", options.archived.toString());
    if (options.active !== undefined)
      params.append("active", options.active.toString());
    if (options.closed !== undefined)
      params.append("closed", options.closed.toString());
    if (options.liquidityNumMin !== undefined)
      params.append("liquidity_num_min", options.liquidityNumMin.toString());
    if (options.volumeNumMin !== undefined)
      params.append("volume_num_min", options.volumeNumMin.toString());
    if (options.startDateMin)
      params.append("start_date_min", options.startDateMin);
    if (options.endDateMin) params.append("end_date_min", options.endDateMin);
  } else {
    // Default filters when no options provided
    params.append("active", "true");
    params.append("closed", "false");
  }

  const url = `https://gamma-api.polymarket.com/markets?${params}`;

  try {
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const rawData = await response.json();

    // Parse the JSON strings in the response
    const data: GammaMarketsResponse = {
      markets: rawData
        .filter((market: RawGammaMarket) => {
          // Only include markets that have clobTokenIds
          const tokens = safeJsonParse<string[]>(market.clobTokenIds, []);
          return tokens.length === 2; // Ensure it's a binary market with both token IDs
        })
        .map((market: RawGammaMarket) => {
          // Create the base market object
          const baseMarket = {
            ...market,
            outcomes: safeJsonParse<string[]>(market.outcomes, []),
            clobTokenIds: safeJsonParse<string[]>(market.clobTokenIds, []),
            outcomePrices: safeJsonParse<string[]>(market.outcomePrices, []),
            volumeNum: parseFloat(market.volume || "0"),
            liquidityNum: parseFloat(market.liquidity || "0"),
            title: market.question,
            endDate: market.endDate,
            startDate: market.startDate,
            imageUrl: market.image,
            category: market.groupItemTitle || "General",
            subcategory: "",
            status: market.closed
              ? "closed"
              : market.active
              ? "active"
              : "inactive",
          };

          return baseMarket;
        }),
    };

    return data;
  } catch (error) {
    console.error("Error fetching Gamma markets:", error);
    throw error;
  }
}
