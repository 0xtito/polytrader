/* <ai_context>
   MarketList component renders a list/grid of MarketCard components.
</ai_context> */
"use client";

import React from "react";
import MarketCard from "./market-card";
import { Market } from "@/lib/actions/polymarket/getMarkets";

interface MarketListProps {
  markets: Market[];
}

export default function MarketList({ markets }: MarketListProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
      {markets.map((market) => (
        <MarketCard key={market.condition_id} market={market} />
      ))}
    </div>
  );
}
