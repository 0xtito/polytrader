"use client";

import React, { useState } from "react";
import { format } from "date-fns";
import {
  ArrowUpIcon,
  ArrowDownIcon,
  ChartAreaIcon,
  BarChart3Icon,
  TimerIcon,
  DollarSignIcon,
} from "lucide-react";
import AgentConsole from "@/components/agent-console";
import { PolymarketData, ParsedMarketData } from "@/types/market-types";
import { cn } from "@/lib/utils";

// Demo market data
const demoMarket: PolymarketData = {
  id: "demo",
  question: "Will the Eagles win Super Bowl 2025?",
  description:
    'This market will resolve to "Yes" if the Philadelphia Eagles win Super Bowl LIX. Otherwise, this market will resolve to "No".\n\nIf at any point it becomes impossible for this team to win the Super Bowl based on the rules of the NFL (e.g. they are eliminated in the playoff bracket), this market will resolve immediately to "No".',
  volume: "10079404.377335",
  volumeNum: 10079404.377335,
  volume24hr: 246630.568942,
  liquidity: "1642645.04094",
  liquidityNum: 1642645.04094,
  outcomes: '["Yes", "No"]',
  outcomePrices: "[0.478, 0.522]",
  endDate: "2025-02-09T12:00:00Z",
  startDate: "2024-07-09T15:37:44.526Z",
  image:
    "https://polymarket-upload.s3.us-east-2.amazonaws.com/will-the-eagles-win-super-bowl-2025-WT_Uuw9p6PPL.png",
  lastTradePrice: 0.479,
  bestBid: 0.477,
  bestAsk: 0.479,
  spread: 0.002,
  oneDayPriceChange: 0.005,
} as PolymarketData;

const parsedDemoMarket: ParsedMarketData = {
  ...demoMarket,
  parsedOutcomes: JSON.parse(demoMarket.outcomes),
  parsedPrices: JSON.parse(demoMarket.outcomePrices),
  parsedClobTokenIds: [],
};

export default function DemoMarketDetailClient() {
  const [agentStarted, setAgentStarted] = useState<boolean>(false);
  const market = parsedDemoMarket;

  const priceChangeColor =
    market.oneDayPriceChange >= 0 ? "text-green-500" : "text-red-500";
  const priceChangeIcon =
    market.oneDayPriceChange >= 0 ? (
      <ArrowUpIcon className="w-4 h-4" />
    ) : (
      <ArrowDownIcon className="w-4 h-4" />
    );

  return (
    <div className="container mx-auto p-6 space-y-6">
      {!agentStarted ? (
        <div className="space-y-6">
          <div className="flex items-start gap-6">
            <div className="w-24 h-24 rounded-lg overflow-hidden">
              <img
                src={market.image}
                alt={market.question}
                className="w-full h-full object-cover"
              />
            </div>
            <div className="flex-1">
              <h1 className="text-3xl font-bold mb-2">{market.question}</h1>
              <p className="text-muted-foreground whitespace-pre-line">
                {market.description}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              icon={<DollarSignIcon className="w-5 h-5" />}
              title="24h Volume"
              value={`$${market.volume24hr.toLocaleString(undefined, {
                maximumFractionDigits: 0,
              })}`}
            />
            <StatCard
              icon={<BarChart3Icon className="w-5 h-5" />}
              title="Total Volume"
              value={`$${market.volumeNum.toLocaleString(undefined, {
                maximumFractionDigits: 0,
              })}`}
            />
            <StatCard
              icon={<ChartAreaIcon className="w-5 h-5" />}
              title="Liquidity"
              value={`$${market.liquidityNum.toLocaleString(undefined, {
                maximumFractionDigits: 0,
              })}`}
            />
            <StatCard
              icon={<TimerIcon className="w-5 h-5" />}
              title="Ends"
              value={format(new Date(market.endDate), "MMM d, yyyy")}
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="rounded-xl border bg-card p-6">
              <h2 className="text-xl font-semibold mb-4">Current Prices</h2>
              <div className="space-y-4">
                {market.parsedOutcomes.map((outcome, index) => (
                  <div
                    key={outcome}
                    className="flex items-center justify-between"
                  >
                    <span className="font-medium">{outcome}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-2xl font-bold">
                        {(market.parsedPrices[index] * 100).toFixed(1)}%
                      </span>
                      {index === 0 && (
                        <span
                          className={cn(
                            "flex items-center text-sm",
                            priceChangeColor
                          )}
                        >
                          {priceChangeIcon}
                          {Math.abs(market.oneDayPriceChange * 100).toFixed(1)}%
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-xl border bg-card p-6">
              <h2 className="text-xl font-semibold mb-4">Order Book</h2>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Best Bid</span>
                  <span className="font-medium">
                    {(market.bestBid * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Best Ask</span>
                  <span className="font-medium">
                    {(market.bestAsk * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Spread</span>
                  <span className="font-medium">
                    {(market.spread * 100).toFixed(2)}%
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div className="flex justify-center">
            <button
              onClick={() => setAgentStarted(true)}
              className="bg-primary text-primary-foreground hover:bg-primary/90 px-8 py-3 rounded-lg font-medium transition-colors"
            >
              Run AI Analysis
            </button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="space-y-6">
            <div className="rounded-xl border bg-card p-6">
              <div className="flex items-start gap-4">
                <img
                  src={market.image}
                  alt={market.question}
                  className="w-16 h-16 rounded-lg"
                />
                <div>
                  <h2 className="text-xl font-semibold">{market.question}</h2>
                  <p className="text-sm text-muted-foreground mt-1">
                    Ends {format(new Date(market.endDate), "MMM d, yyyy")}
                  </p>
                </div>
              </div>
            </div>

            <div className="rounded-xl border bg-card p-6 space-y-4">
              <h3 className="font-semibold">Market Stats</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">24h Volume</p>
                  <p className="font-medium">
                    $
                    {market.volume24hr.toLocaleString(undefined, {
                      maximumFractionDigits: 0,
                    })}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Total Volume</p>
                  <p className="font-medium">
                    $
                    {market.volumeNum.toLocaleString(undefined, {
                      maximumFractionDigits: 0,
                    })}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Current Price</p>
                  <div className="flex items-center gap-2">
                    <p className="font-medium">
                      {(market.lastTradePrice * 100).toFixed(1)}%
                    </p>
                    <span
                      className={cn(
                        "flex items-center text-sm",
                        priceChangeColor
                      )}
                    >
                      {priceChangeIcon}
                      {Math.abs(market.oneDayPriceChange * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Liquidity</p>
                  <p className="font-medium">
                    $
                    {market.liquidityNum.toLocaleString(undefined, {
                      maximumFractionDigits: 0,
                    })}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="lg:row-span-2">
            <AgentConsole marketId={parseInt(market.id)} />
          </div>
        </div>
      )}
    </div>
  );
}

interface StatCardProps {
  icon: React.ReactNode;
  title: string;
  value: string;
}

function StatCard({ icon, title, value }: StatCardProps) {
  return (
    <div className="rounded-xl border bg-card p-6">
      <div className="flex items-center gap-2 text-muted-foreground mb-2">
        {icon}
        <span className="text-sm">{title}</span>
      </div>
      <p className="text-2xl font-bold">{value}</p>
    </div>
  );
}
