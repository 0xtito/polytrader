"use server";

/* <ai_context>
   This file defines a server action to fetch Gamma markets, then filter, sort, and paginate them
   based on user-provided filters.
</ai_context> */

import { getGammaMarkets } from "./get-gamma-markets";
import { AdvancedMarket } from "./getMarkets";

/**
 * Filter and sort fields passed from the FilterBar / DashboardClient
 */
interface MarketFilters {
  volumeMin: string;
  volume24hrMin: string;
  sortBy: "volume" | "volume24hr" | "outcome" | "featured";
  sortOrder: "asc" | "desc";
  page: number;
  limit: number;
  tagId: string;
  featured: boolean;
}

/**
 * Returns a subset of markets (and total pages) after applying filtering, sorting, and pagination.
 * We fetch more or all markets from Gamma (in a loop if needed), then do the logic locally.
 */
export async function getFilteredMarkets(filters: Partial<MarketFilters>) {
  // Set defaults
  const {
    volumeMin = "",
    volume24hrMin = "",
    sortBy = "volume",
    sortOrder = "desc",
    page = 1,
    limit = 12,
    tagId = undefined,
    featured = false,
  } = filters;

  // We'll gather all markets from Gamma. We'll fetch in chunks using offset.
  // If there's a very large set, we can cap it for safety.
  let offset = 0;
  const chunkSize = 200; // retrieve 200 at a time
  const maxFetchCount = 2000; // safety net to avoid excessive requests
  const allMarkets: AdvancedMarket[] = [];

  while (true) {
    const { markets } = await getGammaMarkets(chunkSize, offset, {
      archived: false,
      closed: false,
      active: true,
      tagId,
      relatedTags: true,
      featured,
    });

    allMarkets.push(...markets);

    // If we got fewer than chunkSize, we're done
    if (markets.length < chunkSize) {
      break;
    }

    offset += chunkSize;
    if (offset >= maxFetchCount) {
      break;
    }
  }

  // Now we apply local filters:

  // Convert string-based filters to numbers
  const minVolume = volumeMin ? parseFloat(volumeMin) : 0;
  const minVolume24hr = volume24hrMin ? parseFloat(volume24hrMin) : 0;

  // Filter out markets based on volume and 24h volume
  let filteredMarkets = allMarkets.filter((m) => {
    // parse volume
    const vol = parseFloat(m.volume || "0");
    const vol24hr = (m.volume24hrAmm || 0) + (m.volume24hrClob || 0);

    // filter conditions
    if (vol < minVolume) return false;
    if (vol24hr < minVolume24hr) return false;

    return true;
  });

  // Sorting
  filteredMarkets.sort((a, b) => {
    let valA = 0;
    let valB = 0;

    // parse volumes
    const aVol = parseFloat(a.volume || "0");
    const bVol = parseFloat(b.volume || "0");
    const aVol24hr = (a.volume24hrAmm || 0) + (a.volume24hrClob || 0);
    const bVol24hr = (b.volume24hrAmm || 0) + (b.volume24hrClob || 0);

    // outcome "closeness" from 50%: if outcomePrices is ["0.665","0.335"], pick the first
    // so difference is abs(0.5 - 0.665) = 0.165
    const aOutcomeDiff = Math.abs(
      0.5 - parseFloat(a.outcomePrices?.[0] || "0")
    );
    const bOutcomeDiff = Math.abs(
      0.5 - parseFloat(b.outcomePrices?.[0] || "0")
    );

    if (sortBy === "volume") {
      valA = aVol;
      valB = bVol;
    } else if (sortBy === "volume24hr") {
      valA = aVol24hr;
      valB = bVol24hr;
    } else if (sortBy === "outcome") {
      // smaller difference => closer to 50/50 => sort ascending
      // so valA= aOutcomeDiff
      valA = aOutcomeDiff;
      valB = bOutcomeDiff;
    } else if (sortBy === "featured") {
      // Featured markets should be sorted first
      valA = a.featured ? 1 : 0;
      valB = b.featured ? 1 : 0;
    }

    // if ascending, sort valA < valB => -1
    // if descending, reverse
    if (sortOrder === "asc") {
      return valA - valB;
    } else {
      return valB - valA;
    }
  });

  // Pagination
  const totalMarkets = filteredMarkets.length;
  const totalPages = Math.ceil(totalMarkets / limit);
  const startIndex = (page - 1) * limit;
  const endIndex = startIndex + limit;
  const paginated = filteredMarkets.slice(startIndex, endIndex);

  return {
    markets: paginated,
    totalPages,
  };
}
