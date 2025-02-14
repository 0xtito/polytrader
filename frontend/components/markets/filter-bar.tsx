"use client";

/* <ai_context>
   This FilterBar provides UI for the user to set filters and sorting. 
   We'll add the "Outcome (50/50)" sort option. 
</ai_context> */

import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

type FilterBarProps = {
  onFilterChange: (filters: FilterState) => void;
};

type FilterState = {
  volumeMin: string;
  volume24hrMin: string;
  sortBy: "volume" | "volume24hr" | "outcome";
  sortOrder: "asc" | "desc";
};

export function FilterBar({ onFilterChange }: FilterBarProps) {
  const [filters, setFilters] = useState<FilterState>({
    volumeMin: "",
    volume24hrMin: "",
    sortBy: "volume",
    sortOrder: "desc",
  });

  const handleChange = (key: keyof FilterState, value: string) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  return (
    <div className="flex flex-wrap gap-4 p-4 bg-background rounded-lg shadow">
      <div className="flex flex-col">
        <Label htmlFor="volumeMin">Min Volume</Label>
        <Input
          id="volumeMin"
          type="number"
          value={filters.volumeMin}
          onChange={(e) => handleChange("volumeMin", e.target.value)}
          placeholder="Min Volume"
        />
      </div>

      <div className="flex flex-col">
        <Label htmlFor="volume24hrMin">Min 24h Volume</Label>
        <Input
          id="volume24hrMin"
          type="number"
          value={filters.volume24hrMin}
          onChange={(e) => handleChange("volume24hrMin", e.target.value)}
          placeholder="Min 24h Volume"
        />
      </div>

      <div className="flex flex-col">
        <Label htmlFor="sortBy">Sort By</Label>
        <Select
          value={filters.sortBy}
          onValueChange={(value) => handleChange("sortBy", value)}
        >
          <SelectTrigger id="sortBy">
            <SelectValue placeholder="Sort by" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="volume">Volume</SelectItem>
            <SelectItem value="volume24hr">24h Volume</SelectItem>
            <SelectItem value="outcome">Outcome (50/50)</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="flex flex-col">
        <Label htmlFor="sortOrder">Sort Order</Label>
        <Select
          value={filters.sortOrder}
          onValueChange={(value) =>
            handleChange("sortOrder", value as "asc" | "desc")
          }
        >
          <SelectTrigger id="sortOrder">
            <SelectValue placeholder="Sort order" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="asc">Ascending</SelectItem>
            <SelectItem value="desc">Descending</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}