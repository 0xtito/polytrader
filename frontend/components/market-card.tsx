/* <ai_context>
   MarketCard component displays a summary of a market.
</ai_context> */
"use client";

import React from "react";
import Link from "next/link";

interface Market {
  id: number;
  title: string;
  volume: number;
  createdAt: string;
}

interface MarketCardProps {
  market: Market;
}

export default function MarketCard({ market }: MarketCardProps) {
  return (
    <Link href={`/markets/${market.id}`}>
      <div className="border rounded p-4 hover:shadow-lg transition-shadow cursor-pointer">
        <h2 className="text-lg font-semibold">{market.title}</h2>
        <p className="text-sm text-muted-foreground">Volume: ${market.volume.toLocaleString()}</p>
        <p className="text-xs text-muted-foreground">Created on: {market.createdAt}</p>
      </div>
    </Link>
  );
}