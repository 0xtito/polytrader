# <ai_context>
# This script fetches all active (non-closed) events from Polymarket's GammaMarketClient 
# and writes selected fields (question, category, market_slug) to a JSON file.
# </ai_context>

import os
import json
import argparse
from polytrader.gamma import GammaMarketClient

def main():
    parser = argparse.ArgumentParser(description="Fetch all active Polymarket events and save selected fields to a JSON file.")
    parser.add_argument("--limit", type=int, default=100, help="Number of events to fetch (default=100).")
    parser.add_argument("--offset", type=int, help="Pagination offset.")
    parser.add_argument("--order", type=str, help="Key to sort by.")
    parser.add_argument("--ascending", type=bool, help="Sort direction, defaults to true.")
    parser.add_argument("--tag_id", type=int, help="Filter by tag ID.")
    parser.add_argument("--active", type=bool, default=True, help="Filter by active status.")
    parser.add_argument("--closed", type=bool, default=False, help="Filter by closed status.")
    parser.add_argument("--archived", type=bool, default=False, help="Filter by archived status.")
    parser.add_argument("--output", default="data/active_events.json", help="Path to save the JSON output.")
    args = parser.parse_args()

    gamma = GammaMarketClient()
    
    # Build query parameters
    query_params = {
        "limit": args.limit,
        "active": args.active,
        "closed": args.closed,
        "archived": args.archived
    }
    
    # Add optional parameters if provided
    if args.offset is not None:
        query_params["offset"] = args.offset
    if args.order:
        query_params["order"] = args.order
        if args.ascending is not None:
            query_params["ascending"] = args.ascending
    if args.tag_id is not None:
        query_params["tag_id"] = args.tag_id

    try:
        # Fetch events
        print("Fetching events with parameters:", query_params)
        all_events = gamma.get_events(querystring_params=query_params)
        
        if not all_events:
            print("Warning: No events returned from the API")
            return

        # Process events
        active_events = []
        for event in all_events:
            # Extract markets data
            markets_data = []
            if 'markets' in event:
                for market in event['markets']:
                    try:
                        market_data = {
                            'question': market.get('question'),
                            'conditionId': market.get('conditionId'),
                            'volume': market.get('volume'),
                            'liquidity': market.get('liquidity')
                        }
                        
                        # Safely parse JSON strings
                        try:
                            market_data['outcomePrices'] = json.loads(market.get('outcomePrices', '[]'))
                        except json.JSONDecodeError:
                            market_data['outcomePrices'] = []
                            
                        try:
                            market_data['outcomes'] = json.loads(market.get('outcomes', '[]'))
                        except json.JSONDecodeError:
                            market_data['outcomes'] = []
                            
                        markets_data.append(market_data)
                    except Exception as e:
                        print(f"Warning: Error processing market data: {e}")
                        continue

            event_data = {
                'id': event.get('id'),
                'title': event.get('title'),
                'description': event.get('description'),
                'slug': event.get('slug'),
                'startDate': event.get('startDate'),
                'endDate': event.get('endDate'),
                'volume': event.get('volume'),
                'liquidity': event.get('liquidity'),
                'markets': markets_data,
            }
            # active_events.append(event_data)
            active_events.append(event)

        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        
        # Write to JSON
        with open(args.output, "w") as f:
            json.dump(active_events, f, indent=2)

        # Print result summary
        print(f"\nFetched {len(active_events)} events.")
        print(f"Saved results to {args.output}")
        
        if active_events:
            print("\nSample of events:")
            for event in active_events[:3]:  # Print the first 3 as a sample
                print(f"\nTitle: {event['title']}")
                print(f"Description: {event['description'][:100]}...")  # Truncate long descriptions
                print(f"Number of markets: {len(event['markets'])}")
                if event['markets']:
                    print("Sample market question:", event['markets'][0]['question'])

    except Exception as e:
        print(f"Error: Failed to fetch or process events: {e}")
        raise

if __name__ == "__main__":
    main() 