/* <ai_context>
   MarketList component renders a list/grid of MarketCard components.
</ai_context> */
"use client";

import React from "react";
import MarketCard from "./market-card";

interface Market {
  id: number;
  title: string;
  volume: number;
  createdAt: string;
}

interface MarketListProps {
  markets: Market[];
}

export default function MarketList({ markets }: MarketListProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {markets.map((market) => (
        <MarketCard key={market.id} market={market} />
      ))}
    </div>
  );
}