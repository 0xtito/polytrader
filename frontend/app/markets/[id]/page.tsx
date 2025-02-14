import MarketDetailClient from "./_components/market-detail-client";
import { getGammaMarkets } from "@/lib/actions/polymarket/get-gamma-markets";

export default async function MarketDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = await params;
  const marketId = resolvedParams.id;
  const marketData = await getGammaMarkets(1, 0, { marketId });

  if (!marketData.markets || marketData.markets.length === 0) {
    throw new Error(`Market with ID ${marketId} not found`);
  }

  return (
    <MarketDetailClient
      marketId={marketId}
      initialMarketData={marketData.markets[0]}
    />
  );
}