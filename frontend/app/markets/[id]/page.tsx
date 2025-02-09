import { use } from "react";
import MarketDetailClient from "@/components/market-detail-client";

export default async function MarketDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = await params;
  const marketId = parseInt(resolvedParams.id, 10);

  return <MarketDetailClient marketId={marketId} />;
}
