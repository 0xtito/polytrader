"use client";

import React, { useEffect, useState, useRef, useCallback } from "react";
import { useToast } from "@/hooks/use-toast";
import { Button } from "@/components/ui/button";
import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from "@/components/ui/accordion";

// ---------- Types ----------

interface StreamingAgentConsoleProps {
  isStreaming: boolean;
  streamOutput: string[];
  agentEvents: AgentEvent[];
}

/**
 * Each event from the agent's streamed updates.
 * `name` is the node name: research_agent, analysis_agent, etc.
 * `data` is the payload for that node.
 */
export interface AgentEvent {
  name: string;
  data: {
    messages?: any[];
    market_data?: any;
    metadata?: {
      run_id: string;
      attempt: number;
    };
    external_research_info?: {
      research_summary: string;
      confidence: number;
      source_links: string[];
    };
    analysis_info?: {
      analysis_summary: string;
      confidence: number;
      market_metrics: any;
      orderbook_analysis: any;
      trading_signals: any;
      execution_recommendation: any;
    };
    trade_info?: {
      side: "BUY" | "SELL" | "NO_TRADE";
      market_id: string;
      token_id: string;
      size: number;
      reason: string;
      confidence: number;
      trade_evaluation_of_market_data: string;
    };
  };
}

interface AgentMessage {
  status?: "error" | "success";
  title?: string;
  content: string;
  url?: string;
}

// ---------- Card Components ----------

function FetchMarketDataCard({ data }: { data: any }) {
  const messages = data.messages || [];
  const marketData = data.market_data;

  return (
    <div className="border rounded-lg p-4 bg-white dark:bg-gray-800 shadow">
      <h3 className="font-bold mb-2 text-lg text-primary">
        Market Data Fetched
      </h3>
      {messages.length > 0 && (
        <div className="mb-2">
          {messages.map((msg: string, idx: number) => (
            <p key={idx} className="text-sm">
              {msg}
            </p>
          ))}
        </div>
      )}
      {marketData && (
        <Accordion type="single" collapsible className="w-full">
          <AccordionItem value="market_data">
            <AccordionTrigger>Show Raw Market Data</AccordionTrigger>
            <AccordionContent>
              <pre className="text-xs whitespace-pre-wrap">
                {JSON.stringify(marketData, null, 2)}
              </pre>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      )}
    </div>
  );
}

function ResearchToolsCard({ data }: { data: any }) {
  const messages = data.messages || [];

  return (
    <div className="border rounded-lg p-4 bg-white dark:bg-gray-800 shadow">
      <h3 className="font-bold text-lg text-primary mb-2">Research Tools</h3>

      <Accordion type="single" collapsible className="w-full">
        <AccordionItem value="research_content">
          <AccordionTrigger>Show Research Content</AccordionTrigger>
          <AccordionContent>
            {messages.map((msg: AgentMessage, idx: number) => (
              <div key={idx} className="mb-4">
                {msg.title && (
                  <h4 className="font-semibold text-sm mb-1">{msg.title}</h4>
                )}
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                {msg.url && (
                  <a
                    href={msg.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-blue-600 hover:underline mt-1 block"
                  >
                    Source Link
                  </a>
                )}
              </div>
            ))}
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    </div>
  );
}

function ResearchAgentCard({ data }: { data: any }) {
  const ext = data.external_research_info;

  return (
    <div className="border rounded-lg p-4 bg-white dark:bg-gray-800 shadow">
      <h3 className="font-bold text-lg text-primary mb-2">Research Agent</h3>

      {ext && (
        <>
          <p className="text-sm mb-2">
            <span className="font-semibold">Research Summary:</span>{" "}
            {ext.research_summary}
          </p>

          <p className="text-sm mb-2">
            <span className="font-semibold">Confidence:</span> {ext.confidence}
          </p>

          {ext.source_links && ext.source_links.length > 0 && (
            <Accordion type="single" collapsible className="w-full">
              <AccordionItem value="sources">
                <AccordionTrigger>Show Sources</AccordionTrigger>
                <AccordionContent>
                  <ul className="list-disc list-inside text-sm">
                    {ext.source_links.map((s: string, i: number) => (
                      <li key={i}>
                        <a
                          href={s}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="underline text-blue-600"
                        >
                          {s}
                        </a>
                      </li>
                    ))}
                  </ul>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          )}
        </>
      )}
    </div>
  );
}

function AnalysisAgentCard({ data }: { data: any }) {
  const analysisInfo = data.analysis_info;

  return (
    <div className="border rounded-lg p-4 bg-white dark:bg-gray-800 shadow">
      <h3 className="font-bold text-lg text-primary mb-2">Analysis Agent</h3>

      {analysisInfo && (
        <>
          <p className="text-sm mb-2">
            <span className="font-semibold">Analysis Summary:</span>{" "}
            {analysisInfo.analysis_summary}
          </p>
          <p className="text-sm mb-2">
            <span className="font-semibold">Confidence:</span>{" "}
            {analysisInfo.confidence}
          </p>

          <Accordion type="single" collapsible>
            <AccordionItem value="market_metrics">
              <AccordionTrigger>Market Metrics</AccordionTrigger>
              <AccordionContent>
                <pre className="text-xs whitespace-pre-wrap">
                  {JSON.stringify(analysisInfo.market_metrics, null, 2)}
                </pre>
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="orderbook_analysis">
              <AccordionTrigger>Orderbook Analysis</AccordionTrigger>
              <AccordionContent>
                <pre className="text-xs whitespace-pre-wrap">
                  {JSON.stringify(analysisInfo.orderbook_analysis, null, 2)}
                </pre>
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="trading_signals">
              <AccordionTrigger>Trading Signals</AccordionTrigger>
              <AccordionContent>
                <pre className="text-xs whitespace-pre-wrap">
                  {JSON.stringify(analysisInfo.trading_signals, null, 2)}
                </pre>
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="execution_recommendation">
              <AccordionTrigger>Execution Recommendation</AccordionTrigger>
              <AccordionContent>
                <pre className="text-xs whitespace-pre-wrap">
                  {JSON.stringify(
                    analysisInfo.execution_recommendation,
                    null,
                    2
                  )}
                </pre>
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </>
      )}
    </div>
  );
}

function TradeAgentCard({ data }: { data: any }) {
  const { toast } = useToast();
  const tradeInfo = data.trade_info;
  const messages = data.messages || [];

  if (!tradeInfo) {
    return (
      <div className="border rounded-lg p-4 bg-white dark:bg-gray-800 shadow">
        <h3 className="font-bold text-lg text-primary mb-2">Trade Agent</h3>
        <p className="text-sm">No trade decision yet.</p>
      </div>
    );
  }

  const {
    side,
    reason,
    confidence,
    market_id,
    token_id,
    size,
    trade_evaluation_of_market_data,
  } = tradeInfo;

  const handleBuy = () => {
    toast({
      title: "Purchase in progress",
      description: `Executing BUY for Market ID ${market_id} at size ${size}`,
    });
  };

  const handleNoThanks = () => {
    toast({
      title: "Trade canceled",
      description: "No purchase was made.",
    });
  };

  return (
    <div className="border rounded-lg p-4 bg-white dark:bg-gray-800 shadow space-y-3">
      <h3 className="font-bold text-lg text-primary">Trade Agent</h3>

      <p className="text-sm">
        <span className="font-semibold">Side:</span> {side}
      </p>
      {side !== "NO_TRADE" && (
        <>
          <p className="text-sm">
            <span className="font-semibold">Market ID:</span> {market_id}
          </p>
          <p className="text-sm">
            <span className="font-semibold">Token ID:</span> {token_id}
          </p>
          <p className="text-sm">
            <span className="font-semibold">Size:</span> {size}
          </p>
        </>
      )}
      <p className="text-sm">
        <span className="font-semibold">Confidence:</span> {confidence}
      </p>
      <p className="text-sm mb-2">
        <span className="font-semibold">Reason:</span> {reason}
      </p>

      {trade_evaluation_of_market_data && (
        <p className="text-sm mb-2">
          <span className="font-semibold">Market Evaluation:</span>{" "}
          {trade_evaluation_of_market_data}
        </p>
      )}

      {side === "BUY" ? (
        <div className="flex gap-4">
          <Button variant="default" onClick={handleBuy}>
            Buy
          </Button>
          <Button variant="secondary" onClick={handleNoThanks}>
            No thanks
          </Button>
        </div>
      ) : side === "SELL" ? (
        <div className="flex gap-4">
          <Button variant="default" onClick={handleBuy}>
            Sell
          </Button>
          <Button variant="secondary" onClick={handleNoThanks}>
            No thanks
          </Button>
        </div>
      ) : (
        <div className="flex gap-4">
          <p className="text-sm text-muted-foreground">
            No trade. The agent decided <strong>NO_TRADE</strong>.
          </p>
        </div>
      )}
    </div>
  );
}

function ReflectionCard({ data, agentType }: { data: any; agentType: string }) {
  const messages = data.messages || [];
  const hasErrorOrSuccess = messages.some(
    (m: AgentMessage) => m.status === "error" || m.status === "success"
  );

  if (!hasErrorOrSuccess || messages.length === 0) return null;

  const filteredMessages = messages.filter(
    (m: AgentMessage) => m.status === "error" || m.status === "success"
  );

  if (filteredMessages.length === 0) return null;

  return (
    <div className="ml-8 border-l-2 border-gray-200 pl-4">
      <h4 className="font-semibold text-sm text-gray-600 dark:text-gray-400 mb-2">
        {agentType} Reflection
      </h4>
      <div className="space-y-2">
        {filteredMessages.map((m: AgentMessage, idx: number) => (
          <div
            key={idx}
            className={`p-2 border rounded text-sm ${
              m.status === "error"
                ? "border-red-300 bg-red-50 text-red-700"
                : m.status === "success"
                ? "border-green-300 bg-green-50 text-green-700"
                : ""
            }`}
          >
            {m.content}
          </div>
        ))}
      </div>
    </div>
  );
}

// ---------- The main streaming console component ----------

export default function StreamingAgentConsole({
  isStreaming,
  streamOutput,
  agentEvents,
}: StreamingAgentConsoleProps) {
  const [metadata, setMetadata] = useState<any>(null);
  const [showScrollButton, setShowScrollButton] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    if (containerRef.current) {
      containerRef.current.scrollTo({
        top: containerRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  }, []);

  // Handle auto-scrolling and scroll button visibility
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const handleScroll = () => {
      const { scrollTop, scrollHeight, clientHeight } = container;
      const isNearBottom = scrollHeight - scrollTop - clientHeight < 100;
      setShowScrollButton(!isNearBottom);
    };

    container.addEventListener("scroll", handleScroll);
    return () => container.removeEventListener("scroll", handleScroll);
  }, []);

  // Auto-scroll when new events come in
  useEffect(() => {
    if (!showScrollButton) {
      scrollToBottom();
    }
  }, [agentEvents, showScrollButton, scrollToBottom]);

  // Process streamOutput whenever it changes
  useEffect(() => {
    if (streamOutput && streamOutput.length > 0) {
      try {
        const processedEvents: AgentEvent[] = streamOutput
          .filter((line) => line.trim())
          .map((line) => {
            try {
              const parsed = JSON.parse(line);
              // Extract the node name and data from the parsed line
              const event: AgentEvent = {
                name: parsed.node_name || parsed.type || "unknown",
                data: parsed.data || parsed,
              };
              return event;
            } catch (e) {
              console.error("Error parsing line:", e);
              return null;
            }
          })
          .filter((event): event is AgentEvent => event !== null);

        // If there's metadata in any of the events, update it
        const metadataEvent = processedEvents.find((evt) => evt.data?.metadata);
        if (metadataEvent?.data?.metadata) {
          setMetadata(metadataEvent.data.metadata);
        }
      } catch (e) {
        console.error("Error processing stream output:", e);
      }
    }
  }, [streamOutput]);

  // Example placeholder for an in-progress loading state.
  // This can be triggered if isStreaming is true.
  return (
    <div className="w-full rounded-lg bg-white dark:bg-gray-800 shadow-lg p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">
          AI Agent Analysis
        </h2>
        {isStreaming && (
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
            <span className="text-sm text-gray-500 dark:text-gray-400">
              Streaming...
            </span>
          </div>
        )}
      </div>

      {metadata && (
        <div className="border rounded-lg p-3 bg-gray-50 dark:bg-gray-900 text-sm">
          <p className="font-semibold mb-1">Run ID:</p>
          <p>{metadata.run_id}</p>
          <p className="font-semibold mt-2 mb-1">Attempt:</p>
          <p>{metadata.attempt}</p>
        </div>
      )}

      {!isStreaming && agentEvents.length === 0 && (
        <div className="text-center text-sm text-gray-500 dark:text-gray-400">
          No data yet
        </div>
      )}

      {/* Events container with auto-scroll */}
      <div
        ref={containerRef}
        className="space-y-4 max-h-[32rem] overflow-y-auto custom-scrollbar pr-2 relative"
      >
        {agentEvents.map((evt, idx) => (
          <AgentEventCard key={idx} name={evt.name} data={evt.data} />
        ))}

        {isStreaming && (
          <div className="flex justify-center py-4">
            <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        )}
      </div>

      {/* Scroll to bottom button */}
      {showScrollButton && (
        <button
          onClick={scrollToBottom}
          className="fixed bottom-6 right-6 bg-primary text-primary-foreground rounded-full p-3 shadow-lg hover:bg-primary/90 transition-colors"
        >
          <svg
            className="w-6 h-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 14l-7 7m0 0l-7-7m7 7V3"
            />
          </svg>
        </button>
      )}
    </div>
  );
}

/**
 * Decide which card to show based on the node name (e.g. research_agent, analysis_agent, etc).
 */
function AgentEventCard({ name, data }: { name: string; data: any }) {
  console.log(" --- AgentEventCard ---");
  console.log("NAME: ", name);
  console.log("DATA: ", data);
  switch (name) {
    case "fetch_market_data":
      return <FetchMarketDataCard data={data} />;
    case "research_tools":
      return <ResearchToolsCard data={data} />;
    case "research_agent":
      return <ResearchAgentCard data={data} />;
    case "reflect_on_research":
      return <ReflectionCard data={data} agentType="Research" />;
    case "analysis_agent":
      return <AnalysisAgentCard data={data} />;
    case "reflect_on_analysis":
      return <ReflectionCard data={data} agentType="Analysis" />;
    case "trade_agent":
      return <TradeAgentCard data={data} />;
    case "reflect_on_trade":
      return <ReflectionCard data={data} agentType="Trade" />;
    default:
      // fallback if we don't handle that node
      return (
        <div className="border rounded-lg p-4 bg-white dark:bg-gray-800 shadow">
          <h3 className="font-bold text-lg mb-2">Unknown Node: {name}</h3>
          <pre className="text-xs whitespace-pre-wrap">
            {JSON.stringify(data, null, 2)}
          </pre>
        </div>
      );
  }
}
