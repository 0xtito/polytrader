import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { AdvancedMarket, Token } from "./actions/polymarket/getMarkets";
import { GammaMarket } from "./actions/polymarket/get-gamma-markets";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Convert from GammaMarket to the Market format for MarketList
 * so our existing MarketList can still handle it.
 */
export function mapToFrontendMarkets(
  gammaMarkets: GammaMarket[]
): AdvancedMarket[] {
  return gammaMarkets
    .filter((gm) => gm.outcomes?.length === 2 && gm.clobTokenIds?.length === 2)
    .map((gm) => ({
      condition_id: gm.id.toString(),
      question_id: gm.id.toString(),
      tokens: [
        {
          token_id: gm.clobTokenIds[0],
          outcome: gm.outcomes[0],
        },
        {
          token_id: gm.clobTokenIds[1],
          outcome: gm.outcomes[1],
        },
      ] as [Token, Token],
      outcomePrices: gm.outcomePrices,
      outcomes: gm.outcomes.map((outcome) => ({
        outcome: outcome,
        price: gm.outcomePrices[gm.outcomes.indexOf(outcome)],
      })),
      rewards: {
        min_size: 0,
        max_spread: 0,
        event_start_date: gm.startDate,
        event_end_date: gm.endDate,
        in_game_multiplier: 1,
        reward_epoch: 0,
      },
      minimum_order_size: "1",
      minimum_tick_size: "0.01",
      description: gm.description,
      category: gm.groupItemTitle || "General",
      end_date: gm.endDate,
      end_date_iso: gm.endDate,
      game_start_time: gm.startDate,
      question: gm.question,
      market_slug: gm.slug,
      min_incentive_size: "0",
      max_incentive_spread: "0",
      active: gm.active,
      closed: gm.closed,
      seconds_delay: 0,
      icon: gm.image || "",
      fpmm: "",
      liquidity: gm.liquidity,
      volume: gm.volume,
      volume24hrClob: gm.volume24hrClob,
      volumeClob: gm.volumeClob,
      volume24hrAmm: gm.volume24hrAmm,
      liquidityClob: gm.liquidityClob,
      featured: gm.featured,
    }));
}
