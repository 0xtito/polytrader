import DashboardClient from "../components/dashboard-client";
import { getGammaMarkets } from "@/lib/actions/polymarket/get-gamma-markets";

export default async function Page() {
  const marketsData = await getGammaMarkets(50, undefined, {
    featured: true,
    closed: false,
    order: "liquidityNum",
    ascending: false,
    tagId: "1560",
    relatedTags: true,
    endDateMin: new Date(
      new Date().setDate(new Date().getDate() + 1)
    ).toISOString(),
  });

  return <DashboardClient initialMarkets={marketsData.markets} />;
}
