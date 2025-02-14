// <ai_context>
//   This file defines TypeScript interfaces describing the structure
//   of the data streamed out by our backend agent. These types help ensure
//   a well-typed experience in streaming-agent-console and related components.
// </ai_context>

export interface ReflectionArtifact {
  /**
   * reason: A list of reasons for the reflection's success or failure.
   * Example: ["We validated X, Y, Z...", "We concluded ABC..."]
   */
  reason: string[];

  /**
   * is_satisfactory: Indicates whether the reflection concluded
   * that the information or analysis was acceptable (true) or needs improvement (false).
   */
  is_satisfactory: boolean;

  /**
   * improvement_instructions: If the reflection is not satisfactory,
   * this field contains guidance on what needs to be improved. If it's satisfactory,
   * this will likely be null.
   */
  improvement_instructions: string | null;
}

export interface AgentMessage {
  /**
   * content: The actual text content of this message.
   */
  content: string;

  /**
   * additional_kwargs: Additional fields that may come through the streaming data,
   * including reflection artifacts, tool calls, etc.
   */
  additional_kwargs?: {
    artifact?: ReflectionArtifact;
    // We can add more if needed, e.g. tool call info, etc.
    [key: string]: any;
  };

  /**
   * response_metadata, usage_metadata, etc. that might appear in the message.
   */
  response_metadata?: Record<string, any>;
  usage_metadata?: Record<string, any>;
  type: string;
  name: string | null;
  id: string;
  example?: boolean;
  tool_calls?: ToolCall[];
  invalid_tool_calls?: unknown[];
}

export interface ToolCall {
  /**
   * name: The name of the tool that was called.
   */
  name: string;

  /**
   * args: The arguments that were passed to the tool.
   */
  args?: Record<string, unknown>;

  /**
   * type: The type of the call, often "tool_call".
   */
  type?: string;

  /**
   * id: Unique identifier for this particular tool call.
   */
  id?: string;
}

/**
 * The data for "external_research_info" within the "research_agent" node.
 * This structure can vary, but typically includes a summary, confidence, source links, etc.
 */
export interface ExternalResearchInfo {
  research_summary: string;
  confidence: number;
  source_links?: string[];
}

/**
 * The data for "analysis_info" within the "analysis_agent" node.
 */
export interface AnalysisInfo {
  analysis_summary: string;
  confidence: number;
  market_metrics: {
    price_analysis: string;
    volume_analysis: string;
    liquidity_analysis: string;
  };
  orderbook_analysis: {
    market_depth: string;
    execution_analysis: string;
    liquidity_distribution: string;
  };
  trading_signals: {
    price_momentum: string;
    market_efficiency: string;
    risk_factors: string;
  };
  execution_recommendation: {
    optimal_size: string;
    entry_strategy: string;
    key_levels: string;
  };
}

/**
 * The data for "trade_info" within the "trade_agent" node.
 */
export interface TradeInfo {
  side: "BUY" | "SELL" | "NO_TRADE";
  outcome: "YES" | "NO";
  market_id: string;
  token_id: string;
  size: number;
  reason: string;
  confidence: number;
  trade_evaluation_of_market_data: string;
}

/**
 * Each "event" from the agent's streamed updates.
 * @property name - The node name or event name (e.g., "research_agent", "analysis_agent", "reflect_on_analysis", etc.)
 * @property data - The payload for that node, typically including "messages" plus any extra fields
 */
export interface AgentEvent {
  name: string;
  data: {
    messages?: AgentMessage[];
    metadata?: {
      run_id: string;
      attempt: number;
    };
    external_research_info?: ExternalResearchInfo;
    analysis_info?: AnalysisInfo;
    trade_info?: TradeInfo;
    [key: string]: any;
  };
}

/**
 * The top-level object we receive from the streaming:
 * { event: string; data: Record<string, any> }
 * Typically, "event" might be "metadata" or "updates",
 * with "data" containing sub-objects for each node.
 */
export interface StreamChunk {
  event: string;
  data: Record<string, any>;
}
