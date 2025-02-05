# <ai_context>
# This script fetches currently active Polymarket markets from GammaMarketClient and writes them to a JSON file.
# It also prints out the market IDs and questions, allowing you to pick valid IDs for testing.
# </ai_context>

import os
import json
import argparse
from polytrader.gamma import GammaMarketClient

def main():
    parser = argparse.ArgumentParser(description="Fetch current (active) Polymarket markets and save them to a JSON file.")
    parser.add_argument("--limit", type=int, default=25, help="Number of current markets to fetch (default=25).")
    parser.add_argument("--output", default="data/current_markets.json", help="Path to save the JSON output.")
    args = parser.parse_args()

    gamma = GammaMarketClient()
    # Fetch currently active markets
    markets = gamma.get_current_markets(limit=args.limit)

    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    # Write to JSON
    with open(args.output, "w") as f:
        json.dump(markets, f, indent=2)

    # Print result summary
    print(f"Fetched {len(markets)} current (active) markets.")
    print(f"Saved results to {args.output}")
    print("\nSample of Market IDs and questions:")
    for market in markets[:10]:  # Print the first 10 as a sample
        mid = market.get('id')
        question = market.get('question')
        print(f"  ID: {mid}, Question: {question}")

if __name__ == "__main__":
    main()