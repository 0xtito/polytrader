"use client";

import React, { useEffect, useState } from "react";
import MarketList from "@/components/market-list";
import SortFilterBar from "@/components/sort-filter-bar";

interface Market {
  id: number;
  title: string;
  volume: number;
  createdAt: string;
}

export default function DashboardClient() {
  const [markets, setMarkets] = useState<Market[]>([]);
  const [sortBy, setSortBy] = useState<"volume" | "date">("volume");
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    // Simulate fetching market data
    setLoading(true);
    setTimeout(() => {
      const dummyMarkets: Market[] = [
        {
          id: 1,
          title: "Will Ethereum reach $5000 by 2025?",
          volume: 200000,
          createdAt: "2025-01-05",
        },
        {
          id: 2,
          title: "Will Bitcoin drop below $20000 in 2024?",
          volume: 150000,
          createdAt: "2024-06-10",
        },
        {
          id: 3,
          title: "Will the US adopt digital currency by 2030?",
          volume: 300000,
          createdAt: "2023-11-20",
        },
      ];
      let sortedMarkets = dummyMarkets;
      if (sortBy === "volume") {
        sortedMarkets = dummyMarkets.sort((a, b) => b.volume - a.volume);
      } else {
        sortedMarkets = dummyMarkets.sort(
          (a, b) =>
            new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
        );
      }
      setMarkets([...sortedMarkets]);
      setLoading(false);
    }, 1000);
  }, [sortBy]);

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Prediction Markets</h1>
      <SortFilterBar
        sortBy={sortBy}
        onSortChange={(newSort) => setSortBy(newSort)}
      />
      {loading ? <p>Loading markets...</p> : <MarketList markets={markets} />}
    </div>
  );
}
