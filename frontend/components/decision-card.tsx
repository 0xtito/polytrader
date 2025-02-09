/* <ai_context>
   DecisionCard component displays the final AI recommendation.
</ai_context> */
"use client";

import React from "react";
import { cn } from "@/lib/utils";

interface DecisionCardProps {
  decision: string;
}

export default function DecisionCard({ decision }: DecisionCardProps) {
  const upperDecision = decision.toUpperCase();

  const decisionConfig = {
    BUY: {
      bgColor: "bg-green-500/10 dark:bg-green-500/20",
      textColor: "text-green-700 dark:text-green-300",
      borderColor: "border-green-500/20 dark:border-green-500/30",
      icon: (
        <svg
          className="w-5 h-5 text-green-500"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
          />
        </svg>
      ),
    },
    SELL: {
      bgColor: "bg-red-500/10 dark:bg-red-500/20",
      textColor: "text-red-700 dark:text-red-300",
      borderColor: "border-red-500/20 dark:border-red-500/30",
      icon: (
        <svg
          className="w-5 h-5 text-red-500"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M13 17h8m0 0v-8m0 8l-8-8-4 4-6-6"
          />
        </svg>
      ),
    },
    HOLD: {
      bgColor: "bg-blue-500/10 dark:bg-blue-500/20",
      textColor: "text-blue-700 dark:text-blue-300",
      borderColor: "border-blue-500/20 dark:border-blue-500/30",
      icon: (
        <svg
          className="w-5 h-5 text-blue-500"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
      ),
    },
  };

  const config = decisionConfig[
    upperDecision as keyof typeof decisionConfig
  ] || {
    bgColor: "bg-gray-500/10 dark:bg-gray-500/20",
    textColor: "text-gray-700 dark:text-gray-300",
    borderColor: "border-gray-500/20 dark:border-gray-500/30",
    icon: (
      <svg
        className="w-5 h-5 text-gray-500"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
    ),
  };

  return (
    <div
      className={cn(
        "rounded-lg border p-6 transition-all",
        config.bgColor,
        config.borderColor
      )}
    >
      <div className="flex items-center gap-4 mb-4">
        <div className="p-2 rounded-full bg-white/50 dark:bg-gray-800/50">
          {config.icon}
        </div>
        <div>
          <h3 className={cn("text-lg font-semibold", config.textColor)}>
            AI Recommendation
          </h3>
          <p className="text-2xl font-bold mt-1">{upperDecision}</p>
        </div>
      </div>

      <p className={cn("text-sm leading-relaxed", config.textColor)}>
        Based on comprehensive market analysis and research, our AI system
        recommends to <span className="font-semibold">{upperDecision}</span> in
        this market. This decision is backed by thorough evaluation of market
        conditions, historical trends, and current sentiment indicators.
      </p>
    </div>
  );
}
