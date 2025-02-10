"use client";

import React, { useEffect, useState } from "react";
import { format } from "date-fns";
import {
  ArrowUpIcon,
  ChartAreaIcon,
  BarChart3Icon,
  TimerIcon,
  DollarSignIcon,
} from "lucide-react";
import {
  streamAgentAnalysis,
  writeStreamToFile,
} from "@/lib/actions/stream-agent-analysis";
import StreamingAgentConsole, { AgentEvent } from "./streaming-agent-console";
import { GammaMarket } from "@/lib/actions/get-gamma-markets";

interface MarketDetailClientProps {
  marketId: string;
  initialMarketData: GammaMarket;
}

export default function MarketDetailClient({
  marketId,
  initialMarketData,
}: MarketDetailClientProps) {
  const [market, setMarket] = useState<GammaMarket | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [agentStarted, setAgentStarted] = useState<boolean>(false);
  const [streamOutput, setStreamOutput] = useState<string[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [agentEvents, setAgentEvents] = useState<AgentEvent[]>([]);

  useEffect(() => {
    if (initialMarketData) {
      setMarket(initialMarketData);
      setLoading(false);
    }
  }, [initialMarketData]);

  const handleStartAnalysis = async () => {
    setAgentStarted(true);
    setIsStreaming(true);
    const streamData: any[] = [];

    try {
      const stream = await streamAgentAnalysis(parseInt(marketId));
      let rawStreamData = [];

      // Keep track of successful reflections
      const successfulReflections = new Set<string>();

      for await (const chunk of stream) {
        rawStreamData.push(chunk);

        // Skip metadata events
        if (chunk.event === "metadata") continue;

        if (chunk.event === "updates" && chunk.data) {
          // Process each key in the data object as a separate event
          Object.entries(chunk.data).forEach(([eventName, eventData]) => {
            // Check if this is a successful reflection event
            if (
              eventName.startsWith("reflect_on_") &&
              (
                eventData as { messages?: { status: string }[] }
              )?.messages?.some((m) => m.status === "success")
            ) {
              successfulReflections.add(eventName.replace("reflect_on_", ""));
            }

            const eventInfo = {
              name: eventName,
              data: eventData as Record<string, any>,
              timestamp: new Date().toISOString(),
            };

            streamData.push(eventInfo);

            // Add reflection events always (they can happen multiple times)
            // For non-reflection events, only add if there's no successful reflection yet
            const baseEventName = eventName.replace("reflect_on_", "");
            if (
              eventName.startsWith("reflect_on_") ||
              !successfulReflections.has(baseEventName)
            ) {
              setAgentEvents((prev) => [
                ...prev,
                {
                  name: eventName,
                  data: eventData as Record<string, any>,
                },
              ]);
            }
          });
        }

        setStreamOutput((prev) => [...prev]);
      }

      // Write stream data to file
      await writeStreamToFile(rawStreamData);
    } catch (err) {
      console.error("Streaming error:", err);
      setError(
        err instanceof Error ? err.message : "An error occurred while streaming"
      );
    } finally {
      setIsStreaming(false);
    }
  };

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

  // No price change data in Gamma API
  // const priceChangeColor = "text-gray-500";
  // const _priceChangeIcon = <ArrowUpIcon className="w-4 h-4" />;

  return (
    <div className="container mx-auto p-6 space-y-6">
      {!agentStarted ? (
        <div className="space-y-6">
          <div className="flex items-start gap-6">
            <div className="w-24 h-24 rounded-lg overflow-hidden">
              <img
                src={market.imageUrl}
                alt={market.title}
                className="w-full h-full object-cover"
              />
            </div>
            <div className="flex-1">
              <h1 className="text-3xl font-bold mb-2">{market.title}</h1>
              <p className="text-muted-foreground whitespace-pre-line">
                {market.description}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              icon={<DollarSignIcon className="w-5 h-5" />}
              title="Volume"
              value={`$${market.volumeNum.toLocaleString(undefined, {
                maximumFractionDigits: 0,
              })}`}
            />
            <StatCard
              icon={<BarChart3Icon className="w-5 h-5" />}
              title="Liquidity"
              value={`$${market.liquidityNum.toLocaleString(undefined, {
                maximumFractionDigits: 0,
              })}`}
            />
            <StatCard
              icon={<ChartAreaIcon className="w-5 h-5" />}
              title="Status"
              value={market.status.toUpperCase()}
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
                {market.outcomes.map((outcome, index) => (
                  <div
                    key={outcome}
                    className="flex items-center justify-between"
                  >
                    <span className="font-medium">{outcome}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-2xl font-bold">
                        {(
                          parseFloat(market.outcomePrices[index]) * 100
                        ).toFixed(1)}
                        %
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-xl border bg-card p-6">
              <h2 className="text-xl font-semibold mb-4">Market Info</h2>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Category</span>
                  <span className="font-medium">{market.category}</span>
                </div>
                {market.subcategory && (
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Subcategory</span>
                    <span className="font-medium">{market.subcategory}</span>
                  </div>
                )}
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Order Book</span>
                  <span className="font-medium">
                    {market.enableOrderBook ? "Enabled" : "Disabled"}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div className="flex justify-center">
            <button
              onClick={handleStartAnalysis}
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
                  src={market.imageUrl}
                  alt={market.title}
                  className="w-16 h-16 rounded-lg"
                />
                <div>
                  <h2 className="text-xl font-semibold">{market.title}</h2>
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
                  <p className="text-sm text-muted-foreground">Volume</p>
                  <p className="font-medium">
                    $
                    {market.volumeNum.toLocaleString(undefined, {
                      maximumFractionDigits: 0,
                    })}
                  </p>
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
                <div>
                  <p className="text-sm text-muted-foreground">Status</p>
                  <p className="font-medium">{market.status.toUpperCase()}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Category</p>
                  <p className="font-medium">{market.category}</p>
                </div>
              </div>
            </div>
          </div>

          <div className="lg:row-span-2">
            {error ? (
              <div className="text-red-500">{error}</div>
            ) : (
              <StreamingAgentConsole
                streamOutput={streamOutput}
                isStreaming={isStreaming}
                agentEvents={agentEvents}
              />
            )}
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
