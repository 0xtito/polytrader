"""Data classes for Polymarket objects."""
from __future__ import annotations

from typing import Optional, Union

from pydantic import BaseModel


class Trade(BaseModel):
    """Represents a trade on Polymarket."""

    id: int
    taker_order_id: str
    market: str
    asset_id: str
    side: str
    size: str
    fee_rate_bps: str
    price: str
    status: str
    match_time: str
    last_update: str
    outcome: str
    maker_address: str
    owner: str
    transaction_hash: str
    bucket_index: str
    maker_orders: list[str]
    type: str


class SimpleMarket(BaseModel):
    """A simple market model for Polymarket."""

    id: int
    question: str
    end: str
    description: str
    active: bool
    funded: bool
    rewardsMinSize: float
    rewardsMaxSpread: float
    spread: float
    outcomes: str
    outcome_prices: str
    clob_token_ids: Optional[str]


class ClobReward(BaseModel):
    """Rewards model for the Polymarket CLOB."""

    id: str
    conditionId: str
    assetAddress: str
    rewardsAmount: float
    rewardsDailyRate: int
    startDate: str
    endDate: str


class Tag(BaseModel):
    """Tag metadata for Polymarket events."""

    id: str
    label: Optional[str] = None
    slug: Optional[str] = None
    forceShow: Optional[bool] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    _sync: Optional[bool] = None


class PolymarketEvent(BaseModel):
    """Event metadata on Polymarket."""

    id: str
    ticker: Optional[str] = None
    slug: Optional[str] = None
    title: Optional[str] = None
    startDate: Optional[str] = None
    creationDate: Optional[str] = None
    endDate: Optional[str] = None
    image: Optional[str] = None
    icon: Optional[str] = None
    active: Optional[bool] = None
    closed: Optional[bool] = None
    archived: Optional[bool] = None
    new: Optional[bool] = None
    featured: Optional[bool] = None
    restricted: Optional[bool] = None
    liquidity: Optional[float] = None
    volume: Optional[float] = None
    reviewStatus: Optional[str] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    competitive: Optional[float] = None
    volume24hr: Optional[float] = None
    enableOrderBook: Optional[bool] = None
    liquidityClob: Optional[float] = None
    _sync: Optional[bool] = None
    commentCount: Optional[int] = None
    markets: Optional[list["Market"]] = None
    tags: Optional[list[Tag]] = None
    cyom: Optional[bool] = None
    showAllOutcomes: Optional[bool] = None
    showMarketImages: Optional[bool] = None


class Market(BaseModel):
    """Represents a market with rich metadata on Polymarket."""

    id: int
    question: Optional[str] = None
    conditionId: Optional[str] = None
    slug: Optional[str] = None
    resolutionSource: Optional[str] = None
    endDate: Optional[str] = None
    liquidity: Optional[float] = None
    startDate: Optional[str] = None
    image: Optional[str] = None
    icon: Optional[str] = None
    description: Optional[str] = None
    outcome: Optional[list] = None
    outcomePrices: Optional[list] = None
    volume: Optional[float] = None
    active: Optional[bool] = None
    closed: Optional[bool] = None
    marketMakerAddress: Optional[str] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    new: Optional[bool] = None
    featured: Optional[bool] = None
    submitted_by: Optional[str] = None
    archived: Optional[bool] = None
    resolvedBy: Optional[str] = None
    restricted: Optional[bool] = None
    groupItemTitle: Optional[str] = None
    groupItemThreshold: Optional[int] = None
    questionID: Optional[str] = None
    enableOrderBook: Optional[bool] = None
    orderPriceMinTickSize: Optional[float] = None
    orderMinSize: Optional[int] = None
    volumeNum: Optional[float] = None
    liquidityNum: Optional[float] = None
    endDateIso: Optional[str] = None
    startDateIso: Optional[str] = None
    hasReviewedDates: Optional[bool] = None
    volume24hr: Optional[float] = None
    clobTokenIds: Optional[list] = None
    umaBond: Optional[int] = None
    umaReward: Optional[int] = None
    volume24hrClob: Optional[float] = None
    volumeClob: Optional[float] = None
    liquidityClob: Optional[float] = None
    acceptingOrders: Optional[bool] = None
    negRisk: Optional[bool] = None
    commentCount: Optional[int] = None
    _sync: Optional[bool] = None
    events: Optional[list[PolymarketEvent]] = None
    ready: Optional[bool] = None
    deployed: Optional[bool] = None
    funded: Optional[bool] = None
    deployedTimestamp: Optional[str] = None
    acceptingOrdersTimestamp: Optional[str] = None
    cyom: Optional[bool] = None
    competitive: Optional[float] = None
    pagerDutyNotificationEnabled: Optional[bool] = None
    reviewStatus: Optional[str] = None
    approved: Optional[bool] = None
    clobRewards: Optional[list[ClobReward]] = None
    rewardsMinSize: Optional[int] = None
    rewardsMaxSpread: Optional[float] = None
    spread: Optional[float] = None


class ComplexMarket(BaseModel):
    """Represents a more complex Polymarket object."""

    id: int
    condition_id: str
    question_id: str
    tokens: Union[str, str]
    rewards: str
    minimum_order_size: str
    minimum_tick_size: str
    description: str
    category: str
    end_date_iso: str
    game_start_time: str
    question: str
    market_slug: str
    min_incentive_size: str
    max_incentive_spread: str
    active: bool
    closed: bool
    seconds_delay: int
    icon: str
    fpmm: str
    name: str
    description: Union[str, None] = None
    price: float
    tax: Union[float, None] = None


class SimpleEvent(BaseModel):
    """Represents a simple event on Polymarket."""

    id: int
    ticker: str
    slug: str
    title: str
    description: str
    end: str
    active: bool
    closed: bool
    archived: bool
    restricted: bool
    new: bool
    featured: bool
    restricted: bool  # duplicated field in original code
    markets: str


class Source(BaseModel):
    """Source information for an article."""

    id: Optional[str]
    name: Optional[str]


class Article(BaseModel):
    """Represents an article with optional source information."""

    source: Optional[Source]
    author: Optional[str]
    title: Optional[str]
    description: Optional[str]
    url: Optional[str]
    urlToImage: Optional[str]
    publishedAt: Optional[str]
    content: Optional[str]