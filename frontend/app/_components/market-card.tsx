"use client";

/* <ai_context>
   MarketCard component displays a summary of a market.
</ai_context> */

import React from "react";
import Link from "next/link";
import { Market } from "@/lib/actions/polymarket/getMarkets";
import { format } from "date-fns";

interface MarketCardProps {
  market: Market;
}

export default function MarketCard({ market }: MarketCardProps) {
  return (
    <Link href={`/markets/${market.condition_id}`}>
      <div className="rounded-xl border bg-card p-6 hover:shadow-lg transition-all hover:scale-[1.02]">
        <div className="flex items-start gap-4 mb-4">
          {market.icon && (
            <img
              src={market.icon}
              alt={market.question}
              className="w-12 h-12 rounded-lg object-cover"
            />
          )}
          <div className="flex-1 min-w-0">
            <h2 className="text-xl font-semibold mb-2 line-clamp-2">
              {market.question}
            </h2>
            <p className="text-sm text-muted-foreground line-clamp-2">
              {market.description}
            </p>
          </div>
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Category</span>
            <span className="font-medium">{market.category || "General"}</span>
          </div>

          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Ends</span>
            <span className="font-medium">
              {format(new Date(market.end_date), "MMM d, yyyy")}
            </span>
          </div>

          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Min Order</span>
            <span className="font-medium">
              ${parseFloat(market.minimum_order_size).toLocaleString()}
            </span>
          </div>

          <div className="flex items-center gap-2 pt-2">
            <div
              className={`w-2 h-2 rounded-full ${
                market.active && !market.closed
                  ? "bg-green-500"
                  : market.closed
                  ? "bg-red-500"
                  : "bg-yellow-500"
              }`}
            />
            <span className="text-sm text-muted-foreground">
              {market.closed ? "Closed" : market.active ? "Active" : "Inactive"}
            </span>
          </div>
        </div>
      </div>
    </Link>
  );
}