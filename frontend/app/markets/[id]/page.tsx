import MarketDetailClient from "@/components/market-detail-client";
import { fetchMarketData } from "@/lib/actions/fetchMarketData";

export default async function MarketDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = await params;
  const marketId = resolvedParams.id;
  const marketData = await fetchMarketData(marketId);

  return (
    <MarketDetailClient marketId={marketId} initialMarketData={marketData} />
  );
}
