"use client";

import React, { useEffect, useState } from "react";
import MarketList from "@/components/market-list";
import SortFilterBar from "@/components/sort-filter-bar";
import { Market, Token } from "@/lib/actions/getMarkets";
import { GammaMarket } from "@/lib/actions/get-gamma-markets";

interface DashboardClientProps {
  initialMarkets: GammaMarket[];
}

export default function DashboardClient({
  initialMarkets,
}: DashboardClientProps) {
  const [markets, setMarkets] = useState<GammaMarket[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState<"volume" | "date">("volume");

  useEffect(() => {
    if (initialMarkets) {
      setMarkets(initialMarkets);
      setLoading(false);
    }
  }, [initialMarkets]);

  useEffect(() => {
    if (!markets.length) return;

    let sortedMarkets = [...markets];
    if (sortBy === "volume") {
      sortedMarkets = markets.sort((a, b) => b.volumeNum - a.volumeNum);
    } else {
      sortedMarkets = markets.sort(
        (a, b) => new Date(b.endDate).getTime() - new Date(a.endDate).getTime()
      );
    }
    setMarkets(sortedMarkets);
  }, [sortBy, markets.length]);

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <h1 className="text-3xl font-bold mb-6">Prediction Markets</h1>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </div>
    );
  }

  // Convert GammaMarket to the format expected by MarketList
  const formattedMarkets: Market[] = markets
    .filter((market) => market.outcomes?.length === 2) // Only include binary markets with valid outcomes
    .map((market) => ({
      condition_id: market.id.toString(),
      question_id: market.id.toString(),
      tokens: [
        {
          token_id: market.clobTokenIds[0],
          outcome: market.outcomes[0],
        },
        {
          token_id: market.clobTokenIds[1],
          outcome: market.outcomes[1],
        },
      ] as [Token, Token],
      rewards: {
        min_size: 0,
        max_spread: 0,
        event_start_date: market.startDate,
        event_end_date: market.endDate,
        in_game_multiplier: 1,
        reward_epoch: 0,
      },
      minimum_order_size: "1",
      minimum_tick_size: "0.01",
      description: market.description,
      category: market.category,
      end_date: market.endDate,
      end_date_iso: market.endDate,
      game_start_time: market.startDate,
      question: market.title,
      market_slug: market.slug,
      min_incentive_size: "0",
      max_incentive_spread: "0",
      active: market.active,
      closed: market.closed,
      seconds_delay: 0,
      icon: market.imageUrl || "",
      fpmm: "",
    }));

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Prediction Markets</h1>
      <SortFilterBar
        sortBy={sortBy}
        onSortChange={(newSort) => setSortBy(newSort)}
      />
      <MarketList markets={formattedMarkets} />
    </div>
  );
}
