# <ai_context>
# This script fetches all events from Polymarket's GammaMarketClient and extracts unique tags into a clean JSON format.
# It helps visualize all available tags across active markets.
# </ai_context>

import os
import json
import argparse
from polytrader.gamma import GammaMarketClient

def extract_unique_tags(events, debug=False):
    """Extract unique tags from events and format them nicely."""
    all_tags = {}
    
    for event in events:
        if debug:
            print("--- event ---")
            # print(event)
            # print(event.get("tags"))
        if "tags" in event:
            if debug:
                print("--- tags ---")
                print(event["tags"])
            for tag in event["tags"]:
                if debug:
                    print(tag)
                tag_id = tag.get("id")
                all_tags[tag_id] = {
                    "id": tag.get("id"),
                    "label": tag.get("label", ""),
                    "slug": tag.get("slug", ""),
                    "forceShow": tag.get("forceShow", False),
                    "forceHide": tag.get("forceHide", False),
                    "createdAt": tag.get("createdAt", None),
                    "updatedAt": tag.get("updatedAt", None)
                }
    
    # Convert to list and sort by ID for consistent output
    return sorted(all_tags.values(), key=lambda x: x["id"])

def main():
    parser = argparse.ArgumentParser(description="Fetch all Polymarket events and extract unique tags into a JSON file.")
    parser.add_argument("--limit", type=int, default=1000, help="Number of events to fetch (default=1000).")
    parser.add_argument("--output", default="data/all_tags.json", help="Path to save the JSON output.")
    parser.add_argument("--debug", action="store_true", help="Print debug information")
    args = parser.parse_args()

    query_params = {
        "limit": args.limit,
        "active": True,
        "closed": False,
        "archived": False
    }

    gamma = GammaMarketClient()
    print(f"Fetching up to {args.limit} events...")
    print("Fetching events with parameters:", query_params)

    events = gamma.get_events(querystring_params=query_params)
    
    if args.debug:
        # Print first event's tags as a sample
        if events and len(events) > 0:
            print("\nSample event tags:")
            print("Total events:", len(events))
            print(json.dumps(events[0].get("tags", []), indent=2))

    # Extract unique tags
    unique_tags = extract_unique_tags(events, debug=args.debug)

    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    # Write to JSON
    with open(args.output, "w") as f:
        json.dump(unique_tags, f, indent=2)

    print(f"\nFetched {len(events)} events and extracted {len(unique_tags)} unique tags.")
    print(f"Saved results to {args.output}")
    print("\nTags found:")
    for tag in unique_tags:
        print(f"  {tag['label']} (ID: {tag['id']}, Slug: {tag['slug']})")

if __name__ == "__main__":
    main() 