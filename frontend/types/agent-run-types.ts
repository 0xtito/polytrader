/* <ai_context>
   This file contains TypeScript interfaces describing the shape of the agentic run data
   from the Polymarket AI system.
</ai_context> */

export interface ToolCall {
  name: string;
  args?: Record<string, unknown>;
}

export interface Message {
  content: string;
  additional_kwargs: Record<string, unknown>;
  response_metadata: Record<string, unknown> | null;
  type: string;
  name: string | null;
  id: string;
  example: boolean;
  tool_calls: ToolCall[];
  invalid_tool_calls: unknown[];
  usage_metadata: unknown | null;
}

export interface TradeInfo {
  side: string;
  reason: string;
  confidence: number;
}

export interface AgentRunData {
  messages: Message[];
  trade_info?: TradeInfo;
  loop_step?: number;
}

export interface AgentRunData {
  values: {
    market_id: number;
    external_research_info: {
      research_summary: string;
    };
  };
}
