"use client";

import React, { useEffect, useState, useTransition } from "react";
import { AdvancedMarket } from "@/lib/actions/polymarket/getMarkets";
import { getFilteredMarkets } from "@/lib/actions/polymarket/get-filtered-markets";

import { FilterBar } from "@/app/_components/filter-bar";
import MarketList from "@/app/_components/market-list";
import type { FilterState } from "@/app/_components/filter-bar";

import { mapToFrontendMarkets } from "@/lib/utils";

interface DashboardClientProps {
  /**
   * We can optionally pass some initial markets or skip it.
   * If passed, we show them initially until the user triggers a filter.
   */
  initialMarkets?: AdvancedMarket[];
  tagId?: string;
}

/**
 * A client component that manages filters and pages, then calls a server action for markets.
 */
export default function DashboardClient({
  initialMarkets = [],
  tagId,
}: DashboardClientProps) {
  const [markets, setMarkets] = useState<AdvancedMarket[]>(initialMarkets);
  const [loading, setLoading] = useState(true);

  // pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  // filter states
  const [filters, setFilters] = useState<FilterState>({
    volumeMin: "",
    volume24hrMin: "",
    sortBy: "volume",
    sortOrder: "desc",
    tagId: "all",
  });

  // to handle transitions smoothly
  const [isPending, startTransition] = useTransition();

  /**
   * Fetch markets from server action whenever filters or currentPage changes.
   * Also do so initially if no initial markets were provided.
   */
  useEffect(() => {
    if (!initialMarkets.length) {
      fetchMarkets();
    } else {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (initialMarkets.length) {
      fetchMarkets();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters, currentPage]);

  async function fetchMarkets() {
    setLoading(true);
    startTransition(async () => {
      try {
        const res = await getFilteredMarkets({
          ...filters,
          page: currentPage,
          limit: 12,
          tagId: filters.tagId === "all" ? undefined : filters.tagId,
        });
        setMarkets(res.markets);
        setTotalPages(res.totalPages);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    });
  }

  function handleFilterChange(newFilters: typeof filters) {
    setFilters(newFilters);
    setCurrentPage(1);
  }

  function handlePageChange(newPage: number) {
    if (newPage < 1 || newPage > totalPages) return;
    setCurrentPage(newPage);
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold mb-3 bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
          Polytrader Agent
        </h1>
        <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
          Pick any market, and let Poly do the rest for you.
        </p>
      </div>

      <div className="mb-8">
        <FilterBar onFilterChange={handleFilterChange} />
      </div>

      {loading || isPending ? (
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      ) : (
        <MarketList markets={markets} />
      )}

      {/* Pagination controls */}
      <div className="flex items-center justify-center mt-8 gap-4">
        <button
          className="bg-muted text-muted-foreground px-3 py-2 rounded disabled:opacity-50"
          onClick={() => handlePageChange(currentPage - 1)}
          disabled={currentPage <= 1}
        >
          Prev
        </button>
        <span className="text-sm">
          Page {currentPage} of {totalPages}
        </span>
        <button
          className="bg-muted text-muted-foreground px-3 py-2 rounded disabled:opacity-50"
          onClick={() => handlePageChange(currentPage + 1)}
          disabled={currentPage >= totalPages}
        >
          Next
        </button>
      </div>
    </div>
  );
}
