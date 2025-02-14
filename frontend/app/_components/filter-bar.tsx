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
import { Card } from "@/components/ui/card";

type FilterBarProps = {
  onFilterChange: (filters: FilterState) => void;
};

export type FilterState = {
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
    <Card className="p-6 bg-card/50 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="space-y-2">
          <Label htmlFor="volumeMin" className="text-sm font-medium">
            Min Volume
          </Label>
          <Input
            id="volumeMin"
            type="number"
            value={filters.volumeMin}
            onChange={(e) => handleChange("volumeMin", e.target.value)}
            placeholder="Min Volume"
            className="w-full bg-background/50"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="volume24hrMin" className="text-sm font-medium">
            Min 24h Volume
          </Label>
          <Input
            id="volume24hrMin"
            type="number"
            value={filters.volume24hrMin}
            onChange={(e) => handleChange("volume24hrMin", e.target.value)}
            placeholder="Min 24h Volume"
            className="w-full bg-background/50"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="sortBy" className="text-sm font-medium">
            Sort By
          </Label>
          <Select
            value={filters.sortBy}
            onValueChange={(value) => handleChange("sortBy", value)}
          >
            <SelectTrigger id="sortBy" className="w-full bg-background/50">
              <SelectValue placeholder="Sort by" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="volume">Volume</SelectItem>
              <SelectItem value="volume24hr">24h Volume</SelectItem>
              <SelectItem value="outcome">Outcome (50/50)</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="sortOrder" className="text-sm font-medium">
            Sort Order
          </Label>
          <Select
            value={filters.sortOrder}
            onValueChange={(value) =>
              handleChange("sortOrder", value as "asc" | "desc")
            }
          >
            <SelectTrigger id="sortOrder" className="w-full bg-background/50">
              <SelectValue placeholder="Sort order" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="asc">Ascending</SelectItem>
              <SelectItem value="desc">Descending</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
    </Card>
  );
}
