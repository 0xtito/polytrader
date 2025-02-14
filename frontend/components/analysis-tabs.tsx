"use client";

import React from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import ResearchCard from "@/components/research-card";
import TradeExecutionCard from "@/components/trade-execution-card";
import { cn } from "@/lib/utils";

interface AnalysisTabsProps {
  researchData?: {
    report: string;
    learnings: string[];
    visited_urls?: string[];
  };
  tradeData?: {
    orderID: string;
    takingAmount: string;
    makingAmount: string;
    status: string;
    transactionsHashes: string[];
    success: boolean;
    errorMsg?: string;
  };
}

export default function AnalysisTabs({
  researchData,
  tradeData,
}: AnalysisTabsProps) {
  const [activeTab, setActiveTab] = React.useState<string>(
    researchData ? "research" : "trade"
  );

  return (
    <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
      <TabsList className="grid w-full grid-cols-2">
        <TabsTrigger
          value="research"
          disabled={!researchData}
          className={cn(!researchData && "cursor-not-allowed opacity-50")}
        >
          Research
        </TabsTrigger>
        <TabsTrigger
          value="trade"
          disabled={!tradeData}
          className={cn(!tradeData && "cursor-not-allowed opacity-50")}
        >
          Trade Execution
        </TabsTrigger>
      </TabsList>

      <TabsContent value="research" className="mt-4">
        {researchData && (
          <ResearchCard
            report={researchData.report}
            learnings={researchData.learnings}
            visited_urls={researchData.visited_urls}
          />
        )}
      </TabsContent>

      <TabsContent value="trade" className="mt-4">
        {tradeData && <TradeExecutionCard orderData={tradeData} />}
      </TabsContent>
    </Tabs>
  );
}
