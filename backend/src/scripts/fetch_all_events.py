# <ai_context>
# This script fetches all events from Polymarket's GammaMarketClient and writes them to a JSON file.
# It also prints out some event IDs, allowing you to pick valid IDs for testing.
# </ai_context>

import os
import json
import argparse
from polytrader.gamma import GammaMarketClient

def main():
    parser = argparse.ArgumentParser(description="Fetch all Polymarket events and save them to a JSON file.")
    parser.add_argument("--limit", type=int, default=25, help="Number of events to fetch (default=25).")
    parser.add_argument("--output", default="data/all_events.json", help="Path to save the JSON output.")
    args = parser.parse_args()

    gamma = GammaMarketClient()
    events = gamma.get_events(querystring_params={"limit": args.limit})

    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    # Write to JSON
    with open(args.output, "w") as f:
        json.dump(events, f, indent=2)

    print(f"Fetched {len(events)} events.")
    print(f"Saved results to {args.output}")
    print("\nSample of Event IDs and titles:")
    for event in events[:10]:  # Print the first 10 as a sample
        eid = event.get('id')
        title = event.get('title')
        print(f"  ID: {eid}, Title: {title}")

if __name__ == "__main__":
    main()