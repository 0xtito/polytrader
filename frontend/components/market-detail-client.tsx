"use client";

import React, { useEffect, useState } from "react";
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

interface MarketDetailClientProps {
  marketId: string;
  initialMarketData: PolymarketData;
}

export default function MarketDetailClient({
  marketId,
  initialMarketData,
}: MarketDetailClientProps) {
  const [market, setMarket] = useState<ParsedMarketData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [agentStarted, setAgentStarted] = useState<boolean>(false);

  useEffect(() => {
    if (initialMarketData) {
      // Calculate derived values
      const firstToken = initialMarketData.tokens[0];
      const lastTradePrice = firstToken?.price || 0;

      const parsedMarket: ParsedMarketData = {
        ...initialMarketData,
        parsedOutcomes: initialMarketData.tokens.map((token) => token.outcome),
        parsedPrices: initialMarketData.tokens.map((token) => token.price),
        parsedClobTokenIds: initialMarketData.tokens.map(
          (token) => token.token_id
        ),
        // Set default values for optional fields
        volume24hr: 0,
        volumeNum: 0,
        liquidityNum: 0,
        oneDayPriceChange: 0,
        lastTradePrice,
        bestBid: lastTradePrice * 0.99, // Example default values
        bestAsk: lastTradePrice * 1.01,
        spread: 0.02,
      };
      setMarket(parsedMarket);
      setLoading(false);
    }
  }, [initialMarketData]);

  if (loading || !market) {
    return (
      <div className="w-full h-96 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
          <p className="text-muted-foreground">Loading market data...</p>
        </div>
      </div>
    );
  }

  const priceChangeColor =
    (market.oneDayPriceChange || 0) >= 0 ? "text-green-500" : "text-red-500";
  const priceChangeIcon =
    (market.oneDayPriceChange || 0) >= 0 ? (
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
              value={`$${(market.volume24hr || 0).toLocaleString(undefined, {
                maximumFractionDigits: 0,
              })}`}
            />
            <StatCard
              icon={<BarChart3Icon className="w-5 h-5" />}
              title="Total Volume"
              value={`$${(market.volumeNum || 0).toLocaleString(undefined, {
                maximumFractionDigits: 0,
              })}`}
            />
            <StatCard
              icon={<ChartAreaIcon className="w-5 h-5" />}
              title="Liquidity"
              value={`$${(market.liquidityNum || 0).toLocaleString(undefined, {
                maximumFractionDigits: 0,
              })}`}
            />
            <StatCard
              icon={<TimerIcon className="w-5 h-5" />}
              title="Ends"
              value={format(new Date(market.end_date_iso), "MMM d, yyyy")}
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
                          {Math.abs(
                            (market.oneDayPriceChange || 0) * 100
                          ).toFixed(1)}
                          %
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
                    {((market.bestBid || 0) * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Best Ask</span>
                  <span className="font-medium">
                    {((market.bestAsk || 0) * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Spread</span>
                  <span className="font-medium">
                    {((market.spread || 0) * 100).toFixed(2)}%
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
                    Ends {format(new Date(market.end_date_iso), "MMM d, yyyy")}
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
                    {(market.volume24hr || 0).toLocaleString(undefined, {
                      maximumFractionDigits: 0,
                    })}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Total Volume</p>
                  <p className="font-medium">
                    $
                    {(market.volumeNum || 0).toLocaleString(undefined, {
                      maximumFractionDigits: 0,
                    })}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Current Price</p>
                  <div className="flex items-center gap-2">
                    <p className="font-medium">
                      {((market.lastTradePrice || 0) * 100).toFixed(1)}%
                    </p>
                    <span
                      className={cn(
                        "flex items-center text-sm",
                        priceChangeColor
                      )}
                    >
                      {priceChangeIcon}
                      {Math.abs((market.oneDayPriceChange || 0) * 100).toFixed(
                        1
                      )}
                      %
                    </span>
                  </div>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Liquidity</p>
                  <p className="font-medium">
                    $
                    {(market.liquidityNum || 0).toLocaleString(undefined, {
                      maximumFractionDigits: 0,
                    })}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="lg:row-span-2">
            <AgentConsole marketId={parseInt(marketId)} />
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
