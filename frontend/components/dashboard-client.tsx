"use client";

/* <ai_context>
   DashboardClient fetches and displays markets with sorting & filtering from a server action.
   This replaces the direct getGammaMarkets calls with a dynamic fetch from getFilteredMarkets.
</ai_context> */

import React, { useEffect, useState, useTransition } from "react";
import MarketList from "@/components/market-list";
import SortFilterBar from "@/components/sort-filter-bar";
import { Market, Token } from "@/lib/actions/polymarket/getMarkets";
import { AdvancedMarket } from "@/lib/actions/polymarket/getMarkets";
import { GammaMarket } from "@/lib/actions/polymarket/get-gamma-markets";

// We import getFilteredMarkets server action
import { getFilteredMarkets } from "@/lib/actions/polymarket/get-filtered-markets";
import { FilterBar } from "./markets/filter-bar";

interface DashboardClientProps {
  /**
   * We can optionally pass some initial markets or skip it.
   * If passed, we show them initially until the user triggers a filter.
   */
  initialMarkets?: GammaMarket[];
}

/**
 * A client component that manages filters and pages, then calls a server action for markets.
 */
export default function DashboardClient({
  initialMarkets = [],
}: DashboardClientProps) {
  const [markets, setMarkets] = useState<GammaMarket[]>(initialMarkets);
  const [loading, setLoading] = useState(true);

  // pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  // filter states
  const [filters, setFilters] = useState({
    volumeMin: "",
    volume24hrMin: "",
    sortBy: "volume" as const,
    sortOrder: "desc" as const,
  });

  // to handle transitions smoothly
  const [isPending, startTransition] = useTransition();

  /**
   * Convert from GammaMarket to the Market format for MarketList
   * so our existing MarketList can still handle it.
   */
  function mapToFrontendMarkets(gammaMarkets: GammaMarket[]): AdvancedMarket[] {
    return gammaMarkets
      .filter(
        (gm) => gm.outcomes?.length === 2 && gm.clobTokenIds?.length === 2
      )
      .map((gm) => ({
        condition_id: gm.id.toString(),
        question_id: gm.id.toString(),
        tokens: [
          {
            token_id: gm.clobTokenIds[0],
            outcome: gm.outcomes[0],
          },
          {
            token_id: gm.clobTokenIds[1],
            outcome: gm.outcomes[1],
          },
        ] as [Token, Token],
        outcomePrices: gm.outcomePrices,
        rewards: {
          min_size: 0,
          max_spread: 0,
          event_start_date: gm.startDate,
          event_end_date: gm.endDate,
          in_game_multiplier: 1,
          reward_epoch: 0,
        },
        minimum_order_size: "1",
        minimum_tick_size: "0.01",
        description: gm.description,
        category: gm.groupItemTitle || "General",
        end_date: gm.endDate,
        end_date_iso: gm.endDate,
        game_start_time: gm.startDate,
        question: gm.question,
        market_slug: gm.slug,
        min_incentive_size: "0",
        max_incentive_spread: "0",
        active: gm.active,
        closed: gm.closed,
        seconds_delay: 0,
        icon: gm.image || "",
        fpmm: "",
        liquidity: gm.liquidity,
        volume: gm.volume,
        volume24hrClob: gm.volume24hrClob,
        volumeClob: gm.volumeClob,
        liquidityClob: gm.liquidityClob,
        volume24hrAmm: gm.volume24hrAmm,
      }));
  }

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
      // Once the user modifies filters, we want to re-fetch
      // But if we had initial markets, we only skip the immediate re-fetch
      // so let's do it whenever filters or page changes
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
          limit: 12, // you can set your own limit
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
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Prediction Markets</h1>

      <FilterBar onFilterChange={handleFilterChange} />

      {/* <SortFilterBar
        sortBy={filters.sortBy}
        onSortChange={(sortVal) => {
          setFilters((prev) => ({ ...prev, sortBy: sortVal }));
          setCurrentPage(1);
        }}
      /> */}

      {/* We can build more elaborate filter UI or incorporate an existing FilterBar */}
      {/* For example, let's show a simpler approach */}
      {/* Could re-use FilterBar from /markets/filter-bar if we prefer that style */}

      <div className="mb-4"></div>

      {loading || isPending ? (
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      ) : (
        <MarketList markets={mapToFrontendMarkets(markets)} />
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
