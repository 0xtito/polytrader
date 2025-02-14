import Image from "next/image";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { GammaMarket } from "@/lib/actions/polymarket/get-gamma-markets";

import { AdvancedMarket } from "@/lib/actions/polymarket/getMarkets";

export function MarketCard({ market }: { market: AdvancedMarket }) {
  const outcomePrices = market.outcomePrices;
  const tokens = market.tokens;

  return (
    <Card className="w-full max-w-sm">
      <CardHeader>
        <CardTitle className="text-lg">{market.question}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="aspect-video relative mb-4">
          <Image
            src={market.icon || "/placeholder.svg"}
            alt={market.question}
            fill
            className="object-cover rounded-md"
          />
        </div>
        <div className="space-y-2">
          <p>Volume: ${Number.parseFloat(market.volume).toLocaleString()}</p>
          <p>
            Liquidity: ${Number.parseFloat(market.liquidity).toLocaleString()}
          </p>
          <p>
            Outcomes:{" "}
            {(100 * Number.parseFloat(outcomePrices[0])).toFixed(2) +
              "% " +
              tokens[0].outcome}{" "}
            |{" "}
            {(100 * Number.parseFloat(outcomePrices[1])).toFixed(2) +
              "% " +
              tokens[1].outcome}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
