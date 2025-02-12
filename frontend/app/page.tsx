import DashboardClient from "../components/dashboard-client";
import { getGammaMarkets } from "@/lib/actions/get-gamma-markets";

export default async function Page() {
  const marketsData = await getGammaMarkets(50, undefined, {
    featured: true,
    closed: false,
    order: "liquidityNum",
    ascending: false,
    tagId: "101703",
    relatedTags: true,
    // make this so it is 1 day from todayt
    endDateMin: new Date(
      new Date().setDate(new Date().getDate() + 1)
    ).toISOString(),
  });

  return <DashboardClient initialMarkets={marketsData.markets} />;
}
