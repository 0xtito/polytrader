/* <ai_context>
   SortFilterBar component allows users to switch sorting criteria.
</ai_context> */
"use client";

import React from "react";

interface SortFilterBarProps {
  sortBy: "volume" | "date";
  onSortChange: (sort: "volume" | "date") => void;
}

export default function SortFilterBar({ sortBy, onSortChange }: SortFilterBarProps) {
  return (
    <div className="flex space-x-4 mb-4">
      <button
        className={`px-3 py-1 rounded ${sortBy === "volume" ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}`}
        onClick={() => onSortChange("volume")}
      >
        Volume
      </button>
      <button
        className={`px-3 py-1 rounded ${sortBy === "date" ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}`}
        onClick={() => onSortChange("date")}
      >
        Date
      </button>
    </div>
  );
}