# <ai_context>
# This test file checks the Polymarket class methods from polymarket.py.
# </ai_context>

import random

import pytest

from polytrader.polymarket import Polymarket, SimpleMarket


@pytest.mark.asyncio
async def test_get_all_markets():
    """
    Test retrieving all markets using the Polymarket client.
    Checks basic structure for each returned market.
    """
    poly = Polymarket()
    markets = poly.get_all_markets()
    assert isinstance(markets, list), "Expected a list of SimpleMarket objects"

    if not markets:
        pytest.skip("No markets returned from Polymarket. Skipping further checks.")
    random_market = random.choice(markets)
    assert isinstance(random_market, SimpleMarket), (
        "Expected items to be a SimpleMarket instance"
    )
    assert hasattr(random_market, "id"), "SimpleMarket object missing 'id'"
    assert hasattr(random_market, "question"), "SimpleMarket object missing 'question'"


@pytest.mark.asyncio
async def test_get_random_market_by_token_id():
    """
    Fetch a random market from get_all_markets, then retrieve it by token ID
    using Polymarket.get_market(token_id). Ensures the schema matches expectation.
    """
    poly = Polymarket()
    markets = poly.get_all_markets()

    # Filter to markets that appear to have CLOB token IDs
    markets_with_clob = [
        m for m in markets if m.clob_token_ids and m.clob_token_ids != "[]"
    ]
    if not markets_with_clob:
        pytest.skip("No markets have clob_token_ids. Cannot test get_market(token_id).")

    random_market = random.choice(markets_with_clob)
    assert random_market.clob_token_ids, "Expected a non-empty string of token IDs"

    # In the Polymarket code, clob_token_ids are stored as string, so parse them
    # e.g. '["12345","67890"]'
    token_ids = []
    try:
        token_ids = eval(random_market.clob_token_ids)  # or ast.literal_eval
    except Exception:
        pytest.skip("Failed to parse clob_token_ids. Skipping test.")

    if not token_ids:
        pytest.skip("No valid token IDs found in the random market's clob_token_ids.")

    random_token_id = random.choice(token_ids)
    fetched_market = poly.get_market(random_token_id)
    assert fetched_market, "Polymarket.get_market(token_id) returned no data"
    assert int(fetched_market["id"]) == random_market.id, (
        "Market ID mismatch between token ID fetch and original market"
    )


@pytest.mark.asyncio
async def test_get_all_events():
    """
    Test retrieving all events using the Polymarket client.
    Expects a list of SimpleEvent objects. Validates basic fields.
    """
    poly = Polymarket()
    events = poly.get_all_events()
    assert isinstance(events, list), "Expected a list of events"
    if events:
        first = events[0]
        for field_name in ("id", "title", "active", "closed"):
            assert hasattr(first, field_name), f"Expected event to have '{field_name}'"
