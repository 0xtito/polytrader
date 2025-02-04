# <ai_context>
# This test file checks the GammaMarketClient methods for fetching Polymarket data.
# </ai_context>

import random

import pytest

from polytrader.gamma import GammaMarketClient


@pytest.mark.asyncio
async def test_get_all_current_markets():
    """
    Test fetching all current (active) markets from Polymarket via GammaMarketClient.
    We'll limit the number of markets, then pick one random market to retrieve individually.
    """
    gamma_client = GammaMarketClient()
    all_current = gamma_client.get_all_current_markets(limit=5)
    assert all_current is not None, "Expected a non-empty list of markets"
    assert isinstance(all_current, list), "Expected a list response"

    if len(all_current) == 0:
        pytest.skip(
            "No current markets returned. Cannot proceed with random market test."
        )

    # Pick a random market
    random_market = random.choice(all_current)
    assert hasattr(random_market, "id"), (
        "Expected market object to have an 'id' attribute"
    )

    # Now fetch the market again by ID
    fetched_market = gamma_client.get_market(random_market.id)
    assert fetched_market is not None, "Expected a valid market response"
    assert str(fetched_market["id"]) == str(random_market.id), (
        "Market ID mismatch between list and single fetch"
    )


@pytest.mark.asyncio
async def test_get_clob_tradable_markets():
    """
    Test fetching markets that have 'enableOrderBook=True', meaning they are tradable on the CLOB.
    """
    gamma_client = GammaMarketClient()
    tradable_markets = gamma_client.get_clob_tradable_markets(limit=5)
    assert isinstance(tradable_markets, list), "Expected a list of markets"
    for market in tradable_markets:
        assert hasattr(market, "enableOrderBook"), (
            "Expected 'enableOrderBook' field in market object"
        )
        assert market.enableOrderBook is True, "Market should be CLOB tradable"
