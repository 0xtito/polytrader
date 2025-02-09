"use client";

import React, { useEffect, useState } from "react";
import MarketList from "@/components/market-list";
import SortFilterBar from "@/components/sort-filter-bar";
import { Market } from "@/lib/actions/getMarkets";

interface DashboardClientProps {
  initialMarkets: Market[];
}

export default function DashboardClient({
  initialMarkets,
}: DashboardClientProps) {
  const [markets, setMarkets] = useState<Market[]>(initialMarkets);
  const [sortBy, setSortBy] = useState<"volume" | "date">("volume");

  useEffect(() => {
    let sortedMarkets = [...markets];
    if (sortBy === "volume") {
      sortedMarkets = markets.sort(
        (a, b) =>
          parseFloat(b.min_incentive_size) - parseFloat(a.min_incentive_size)
      );
    } else {
      sortedMarkets = markets.sort(
        (a, b) =>
          new Date(b.end_date_iso).getTime() -
          new Date(a.end_date_iso).getTime()
      );
    }
    setMarkets(sortedMarkets);
  }, [sortBy]);

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Prediction Markets</h1>
      <SortFilterBar
        sortBy={sortBy}
        onSortChange={(newSort) => setSortBy(newSort)}
      />
      <MarketList markets={markets} />
    </div>
  );
}
