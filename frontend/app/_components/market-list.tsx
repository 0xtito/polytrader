"use client";

/* <ai_context>
   MarketList displays a list of MarketCard components.
</ai_context> */

import React from "react";
import { AdvancedMarket } from "@/lib/actions/polymarket/getMarkets";
import MarketCard from "@/app/_components/market-card";

interface MarketListProps {
  markets: AdvancedMarket[];
}

export default function MarketList({ markets }: MarketListProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
      {markets.map((market) => (
        <MarketCard key={market.condition_id} market={market} />
      ))}
    </div>
  );
}