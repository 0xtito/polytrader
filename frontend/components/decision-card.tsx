/* <ai_context>
   DecisionCard component displays the final AI recommendation.
</ai_context> */
"use client";

import React from "react";

interface DecisionCardProps {
  decision: string;
}

export default function DecisionCard({ decision }: DecisionCardProps) {
  let bgColor = "bg-secondary";
  if (decision.toUpperCase() === "BUY") {
    bgColor = "bg-green-500";
  } else if (decision.toUpperCase() === "SELL") {
    bgColor = "bg-red-500";
  } else if (decision.toUpperCase() === "HOLD") {
    bgColor = "bg-gray-500";
  }
  return (
    <div className={`mt-4 p-4 rounded ${bgColor} text-white`}>
      <h3 className="text-xl font-bold">Recommendation: {decision.toUpperCase()}</h3>
      <p>Based on the analysis, the AI recommends to {decision.toUpperCase()}.</p>
    </div>
  );
}