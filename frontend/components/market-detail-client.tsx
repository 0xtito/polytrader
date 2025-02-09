"use client";

import React, { useEffect, useState } from "react";
import AgentConsole from "@/components/agent-console";

interface MarketDetail {
  id: number;
  title: string;
  volume: number;
  currentOdds: { yes: number; no: number };
  createdAt: string;
  description: string;
}

interface MarketDetailClientProps {
  marketId: number;
}

export default function MarketDetailClient({
  marketId,
}: MarketDetailClientProps) {
  const [market, setMarket] = useState<MarketDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [agentStarted, setAgentStarted] = useState<boolean>(false);

  useEffect(() => {
    // Simulate fetching market detail data
    setLoading(true);
    setTimeout(() => {
      const dummyMarket: MarketDetail = {
        id: marketId,
        title: "Will Ethereum reach $5000 by 2025?",
        volume: 200000,
        currentOdds: { yes: 0.65, no: 0.35 },
        createdAt: "2025-01-05",
        description:
          "This market tracks whether Ethereum's price will exceed $5000 in 2025.",
      };
      setMarket(dummyMarket);
      setLoading(false);
    }, 1000);
  }, [marketId]);

  if (loading || !market) {
    return <div className="p-4">Loading market details...</div>;
  }

  return (
    <div className="p-4">
      {!agentStarted ? (
        <div>
          <h1 className="text-2xl font-bold mb-2">{market.title}</h1>
          <div className="mb-4">
            <p>
              <strong>Volume:</strong> ${market.volume.toLocaleString()}
            </p>
            <p>
              <strong>Odds:</strong> Yes:{" "}
              {(market.currentOdds.yes * 100).toFixed(0)}% | No:{" "}
              {(market.currentOdds.no * 100).toFixed(0)}%
            </p>
            <p>
              <strong>Description:</strong> {market.description}
            </p>
          </div>
          <button
            className="px-4 py-2 bg-primary text-primary-foreground rounded"
            onClick={() => setAgentStarted(true)}
          >
            Run AI Analysis
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="md:col-span-1 border p-4 rounded">
            <h2 className="text-xl font-bold mb-2">Market Info</h2>
            <p>
              <strong>Title:</strong> {market.title}
            </p>
            <p>
              <strong>Volume:</strong> ${market.volume.toLocaleString()}
            </p>
            <p>
              <strong>Odds:</strong> Yes:{" "}
              {(market.currentOdds.yes * 100).toFixed(0)}% | No:{" "}
              {(market.currentOdds.no * 100).toFixed(0)}%
            </p>
            <p>
              <strong>Description:</strong> {market.description}
            </p>
            <button
              className="mt-4 px-3 py-1 bg-secondary text-secondary-foreground rounded"
              onClick={() => window.location.reload()}
            >
              Refresh Market Data
            </button>
          </div>
          <div className="md:col-span-1 border p-4 rounded">
            <AgentConsole marketId={market.id} />
          </div>
        </div>
      )}
    </div>
  );
}
