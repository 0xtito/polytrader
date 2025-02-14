/* <ai_context>
   MarketList component renders a list/grid of MarketCard components.
</ai_context> */
"use client";

import React from "react";
import { MarketCard } from "@/components/markets/market-card";
import { Market } from "@/lib/actions/polymarket/getMarkets";
import { AdvancedMarket } from "@/lib/actions/polymarket/getMarkets";
import Link from "next/link";

interface MarketListProps {
  markets: AdvancedMarket[];
}

export default function MarketList({ markets }: MarketListProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
      {markets.map((market) => (
        <Link
          key={market.condition_id}
          href={`/markets/${market.condition_id}`}
        >
          <MarketCard market={market} />
        </Link>
      ))}
    </div>
  );
}
