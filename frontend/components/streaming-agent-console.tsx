/* <ai_context>
   AgentConsole component streams real-time AI agent analysis output.
   Now updated to use typed interfaces from agent-stream-types.ts
   and to color-code reflection artifacts based on is_satisfactory.
</ai_context> */
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

// Import the newly created types
import {
  AgentEvent,
  AgentMessage,
  ExternalResearchInfo,
  AnalysisInfo,
  TradeInfo,
  ReflectionArtifact,
  StreamChunk,
} from "@/types/agent-stream-types";

/**
 * Each event from the agent's streamed updates is stored in `agentEvents`.
 * `streamOutput` is the raw output (lines) from the streaming if we want to debug.
 */
interface StreamingAgentConsoleProps {
  isStreaming: boolean;
  streamOutput: string[];
  agentEvents: AgentEvent[];
  onTradeConfirmation?: (decision: "YES" | "NO") => void;
}

/**
 * We'll display each AgentEvent as a card or sub-card, depending on the node name.
 * Some events may contain reflection artifacts that we color-code.
 */

export default function StreamingAgentConsole({
  isStreaming,
  streamOutput,
  agentEvents,
  onTradeConfirmation,
}: StreamingAgentConsoleProps) {
  const [showTradeConfirmation, setShowTradeConfirmation] = useState(false);
  const [tradeToConfirm, setTradeToConfirm] = useState<TradeInfo | null>(null);
  const [metadata, setMetadata] = useState<{
    run_id: string;
    attempt: number;
  } | null>(null);
  const [showScrollButton, setShowScrollButton] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const { dismiss } = useToast();

  const scrollToBottom = useCallback(() => {
    if (containerRef.current) {
      containerRef.current.scrollTo({
        top: containerRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  }, []);

  // Handle scroll button visibility
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

  // Auto-scroll to bottom if user hasn't manually scrolled away
  useEffect(() => {
    if (!showScrollButton) {
      scrollToBottom();
    }
  }, [agentEvents, showScrollButton, scrollToBottom]);

  // Check for trade events that need confirmation
  useEffect(() => {
    const lastEvent = agentEvents[agentEvents.length - 1];
    if (lastEvent?.name === "trade_agent" && lastEvent?.data?.trade_info) {
      const tradeInfo = lastEvent.data.trade_info as TradeInfo;
      if (tradeInfo.side !== "NO_TRADE") {
        setTradeToConfirm(tradeInfo);
        setShowTradeConfirmation(true);
      }
    }
  }, [agentEvents]);

  const handleTradeDecision = (decision: "YES" | "NO") => {
    setShowTradeConfirmation(false);
    setTradeToConfirm(null);
    onTradeConfirmation?.(decision);
  };

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

      {showTradeConfirmation && tradeToConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-xl max-w-md w-full mx-4">
            <h3 className="text-xl font-bold mb-4">Confirm Trade</h3>
            <div className="space-y-4 mb-6">
              <p className="text-gray-600 dark:text-gray-300">
                Would you like to proceed with the following trade?
              </p>
              <div className="bg-gray-50 dark:bg-gray-900 p-4 rounded-lg space-y-2">
                <p>
                  <span className="font-semibold">Side:</span>{" "}
                  {tradeToConfirm.side}
                </p>
                <p>
                  <span className="font-semibold">Size:</span>{" "}
                  {tradeToConfirm.size}
                </p>
                <p>
                  <span className="font-semibold">Confidence:</span>{" "}
                  {tradeToConfirm.confidence}
                </p>
                <p>
                  <span className="font-semibold">Reason:</span>{" "}
                  {tradeToConfirm.reason}
                </p>
              </div>
            </div>
            <div className="flex justify-end gap-4">
              <Button
                variant="outline"
                onClick={() => handleTradeDecision("NO")}
              >
                Reject
              </Button>
              <Button
                onClick={() => handleTradeDecision("YES")}
                className="bg-primary hover:bg-primary/90"
              >
                Accept
              </Button>
            </div>
          </div>
        </div>
      )}

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
 * AgentEventCard decides how to render each event node based on `name` (e.g. "research_agent").
 */
function AgentEventCard({
  name,
  data,
}: {
  name: string;
  data: AgentEvent["data"];
}) {
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
      // fallback
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

/* ============================ */
/* CARDS / COMPONENTS BY NODE  */
/* ============================ */

/** 1) fetch_market_data node */
function FetchMarketDataCard({ data }: { data: AgentEvent["data"] }) {
  const messages = data.messages || [];
  const marketData = data.market_data;

  return (
    <div className="border rounded-lg p-4 bg-white dark:bg-gray-800 shadow">
      <h3 className="font-bold mb-2 text-lg text-primary">
        Market Data Fetched
      </h3>
      {messages.length > 0 && (
        <div className="mb-2">
          {messages.map((msg: AgentMessage, idx: number) => (
            <p key={idx} className="text-sm">
              {msg.content}
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

/** 2) research_tools node */
function ResearchToolsCard({ data }: { data: AgentEvent["data"] }) {
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
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              </div>
            ))}
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    </div>
  );
}

/** 3) research_agent node */
function ResearchAgentCard({ data }: { data: AgentEvent["data"] }) {
  const ext = data.external_research_info as ExternalResearchInfo | undefined;

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

/** 4) reflection nodes (reflect_on_research, reflect_on_analysis, reflect_on_trade, etc.) */
function ReflectionCard({
  data,
  agentType,
}: {
  data: AgentEvent["data"];
  agentType: string;
}) {
  const messages = data.messages || [];

  // We'll look for reflection artifacts in the messages
  // Typically it's in the "additional_kwargs.artifact"
  // We will display them color-coded by is_satisfactory
  const reflectionMessages = messages.filter((m: AgentMessage) => {
    return m.additional_kwargs?.artifact;
  });

  if (reflectionMessages.length === 0) {
    // No reflection artifact found
    return (
      <div className="border rounded-lg p-4 bg-white dark:bg-gray-800 shadow">
        <h3 className="font-bold text-lg text-primary mb-2">
          {agentType} Reflection
        </h3>
        <p className="text-sm">No reflection artifact found.</p>
      </div>
    );
  }

  return (
    <div className="border rounded-lg p-4 bg-white dark:bg-gray-800 shadow">
      <h3 className="font-bold text-lg text-primary mb-2">
        {agentType} Reflection
      </h3>
      <div className="space-y-4">
        {reflectionMessages.map((msg, idx) => {
          const art = msg.additional_kwargs?.artifact as ReflectionArtifact;
          const { is_satisfactory, improvement_instructions } = art;

          return (
            <div key={idx}>
              <p
                className={
                  "p-3 rounded text-sm " +
                  (is_satisfactory
                    ? "bg-green-50 text-green-800 border border-green-300"
                    : "bg-red-50 text-red-800 border border-red-300")
                }
              >
                {msg.content}
              </p>

              {/* If not satisfactory, show improvement instructions */}
              {!is_satisfactory && improvement_instructions && (
                <p className="text-sm text-red-600 mt-2">
                  <strong>Improvement Needed:</strong>{" "}
                  {improvement_instructions}
                </p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

/** 5) analysis_agent node */
function AnalysisAgentCard({ data }: { data: AgentEvent["data"] }) {
  const analysisInfo = data.analysis_info as AnalysisInfo | undefined;

  if (!analysisInfo) {
    return (
      <div className="border rounded-lg p-4 bg-white dark:bg-gray-800 shadow">
        <h3 className="font-bold text-lg text-primary mb-2">Analysis Agent</h3>
        <p className="text-sm">No analysis info yet.</p>
      </div>
    );
  }

  return (
    <div className="border rounded-lg p-4 bg-white dark:bg-gray-800 shadow">
      <h3 className="font-bold text-lg text-primary mb-2">Analysis Agent</h3>
      <p className="text-sm mb-2">
        <span className="font-semibold">Summary:</span>{" "}
        {analysisInfo.analysis_summary}
      </p>
      <p className="text-sm mb-2">
        <span className="font-semibold">Confidence:</span>{" "}
        {analysisInfo.confidence}
      </p>
      <Accordion type="multiple" className="mt-4">
        <AccordionItem value="metrics">
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
              {JSON.stringify(analysisInfo.execution_recommendation, null, 2)}
            </pre>
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    </div>
  );
}

/** 6) trade_agent node */
function TradeAgentCard({ data }: { data: AgentEvent["data"] }) {
  const tradeInfo = data.trade_info as TradeInfo | undefined;
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
      {side === "NO_TRADE" && (
        <p className="text-sm text-muted-foreground">
          No position taken. (side=NO_TRADE)
        </p>
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
    </div>
  );
}
