# <ai_context>
# This script fetches all markets from Polymarket's GammaMarketClient and writes them to a JSON file.
# It also prints out the market IDs and questions, allowing you to pick valid IDs for testing.
# </ai_context>

import os
import json
import argparse
from polytrader.gamma import GammaMarketClient

def main():
    parser = argparse.ArgumentParser(description="Fetch all Polymarket markets and save them to a JSON file.")
    parser.add_argument("--limit", type=int, default=25, help="Number of markets to fetch (default=25).")
    parser.add_argument("--output", default="data/all_markets.json", help="Path to save the JSON output.")
    args = parser.parse_args()

    gamma = GammaMarketClient()
    # Fetch the specified number of markets
    markets = gamma.get_markets(querystring_params={"limit": args.limit})

    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    # Write to JSON
    with open(args.output, "w") as f:
        json.dump(markets, f, indent=2)

    # Print result summary
    print(f"Fetched {len(markets)} markets.")
    print(f"Saved results to {args.output}")
    print("\nSample of Market IDs and questions:")
    for market in markets[:10]:  # Print the first 10 as a sample
        mid = market.get('id')
        question = market.get('question')
        print(f"  ID: {mid}, Question: {question}")

if __name__ == "__main__":
    main()