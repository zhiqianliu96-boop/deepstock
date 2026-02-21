"""
Sentiment analysis service.

Fetches news via Tavily, scores articles with the keyword-based
SentimentScorer, and produces a composite SentimentScore.
"""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass, field
from typing import Any

from app.analyzers.sentiment_scorer import (
    CATEGORY_EARNINGS,
    CATEGORY_INSIDER,
    CATEGORY_POLICY,
    SentimentScorer,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Attempt to import optional dependencies
# ---------------------------------------------------------------------------

try:
    from app.config import settings as _settings

    _TAVILY_API_KEY: str = getattr(_settings, "TAVILY_API_KEY", "") or ""
except Exception:
    _TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")

try:
    from tavily import TavilyClient  # type: ignore[import-untyped]

    _TAVILY_AVAILABLE = True
except ImportError:
    _TAVILY_AVAILABLE = False
    TavilyClient = None  # type: ignore[assignment,misc]

try:
    from app.services.data_fetcher import StockData  # type: ignore[import-untyped]
except ImportError:
    StockData = None  # type: ignore[assignment,misc]


# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------

@dataclass
class SentimentScore:
    """Composite sentiment score for a stock (total 0-100)."""

    total: float = 50.0                         # 0-100
    news_sentiment_score: float = 20.0          # 0-40
    event_impact_score: float = 15.0            # 0-30
    market_attention_score: float = 7.5         # 0-15
    source_quality_score: float = 7.5           # 0-15
    breakdown: dict = field(default_factory=dict)
    articles: list = field(default_factory=list)
    timeline: list = field(default_factory=list)
    category_summary: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# NewsFetcher
# ---------------------------------------------------------------------------

class NewsFetcher:
    """Fetch news articles from Tavily search API."""

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or _TAVILY_API_KEY
        self._client: Any | None = None
        if self._api_key and _TAVILY_AVAILABLE:
            self._client = TavilyClient(api_key=self._api_key)

    # --------------------------------------------------------------------- #

    async def fetch_news(
        self,
        code: str,
        name: str,
        market: str,
    ) -> list[dict]:
        """Fetch recent news articles for the given stock.

        Parameters
        ----------
        code : str
            Stock ticker / code (e.g. "AAPL", "600519").
        name : str
            Company name or short name.
        market : str
            One of "CN", "US", "HK" (case-insensitive).

        Returns
        -------
        list[dict]
            Each dict: {title, content, url, published_date, source}.
        """
        if not self._api_key:
            logger.warning(
                "TAVILY_API_KEY is not set — skipping news fetch. "
                "Sentiment analysis will return a neutral score."
            )
            return []

        if not _TAVILY_AVAILABLE:
            logger.warning(
                "tavily package is not installed — skipping news fetch. "
                "Install with: pip install tavily-python"
            )
            return []

        queries = self._build_queries(code, name, market)
        all_articles: list[dict] = []
        seen_urls: set[str] = set()

        for query in queries:
            try:
                # Tavily's search is synchronous; run in executor to avoid
                # blocking the event loop.
                results = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda q=query: self._client.search(  # type: ignore[union-attr]
                        query=q,
                        max_results=5,
                        include_answer=False,
                    ),
                )

                for item in results.get("results", []):
                    url = item.get("url", "")
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)
                    all_articles.append({
                        "title": item.get("title", ""),
                        "content": item.get("content", ""),
                        "url": url,
                        "published_date": item.get("published_date", ""),
                        "source": item.get("source", ""),
                    })
            except Exception:
                logger.exception("Tavily search failed for query: %s", query)
                # Continue with remaining queries; return partial results.

        return all_articles

    # --------------------------------------------------------------------- #

    @staticmethod
    def _build_queries(code: str, name: str, market: str) -> list[str]:
        """Build a list of search queries tailored to the market."""
        market_upper = market.upper()

        if market_upper == "CN":
            return [
                f"{name} 最新消息",
                f"{name} 研报 分析",
                f"{code} 风险 公告",
            ]
        elif market_upper == "HK":
            return [
                f"{name} stock news Hong Kong",
                f"{code}.HK analysis",
            ]
        else:
            # Default to US-style queries
            return [
                f"{code} {name} stock news",
                f"{code} earnings analyst rating",
                f"{code} stock risk",
            ]


# ---------------------------------------------------------------------------
# SentimentService
# ---------------------------------------------------------------------------

class SentimentService:
    """Orchestrates news fetching and sentiment scoring."""

    def __init__(self) -> None:
        self._fetcher = NewsFetcher()
        self._scorer = SentimentScorer()

    async def analyze(self, stock_data: Any) -> SentimentScore:
        """Run full sentiment analysis for a stock.

        Parameters
        ----------
        stock_data
            An object (typically ``StockData``) with at least ``.code``,
            ``.name``, and ``.market`` attributes.

        Returns
        -------
        SentimentScore
        """
        code: str = getattr(stock_data, "code", "")
        name: str = getattr(stock_data, "name", "")
        market: str = getattr(stock_data, "market", "US")

        # ---- Fetch news ------------------------------------------------- #
        articles = await self._fetcher.fetch_news(code, name, market)

        # If no articles at all, return a neutral score.
        if not articles:
            return SentimentScore(
                total=50.0,
                news_sentiment_score=20.0,
                event_impact_score=15.0,
                market_attention_score=7.5,
                source_quality_score=7.5,
                breakdown={
                    "note": "No news articles available — returning neutral score",
                },
                articles=[],
                timeline=[],
                category_summary={},
            )

        # ---- Score articles --------------------------------------------- #
        scored_articles = self._scorer.score_batch(articles)
        aggregate = self._scorer.compute_aggregate(scored_articles)

        # ---- Sub-scores ------------------------------------------------- #
        news_sentiment = self._calc_news_sentiment(aggregate["overall_score"])
        event_impact = self._calc_event_impact(
            scored_articles, aggregate["category_scores"]
        )
        market_attention = self._calc_market_attention(
            aggregate["article_count"],
            aggregate["overall_score"],
        )
        source_quality = self._calc_source_quality(scored_articles)

        total = round(
            news_sentiment + event_impact + market_attention + source_quality, 2
        )
        total = max(0.0, min(100.0, total))

        # ---- Timeline --------------------------------------------------- #
        timeline = self._build_timeline(scored_articles)

        # ---- Category summary ------------------------------------------- #
        category_summary = self._build_category_summary(scored_articles)

        # ---- Breakdown -------------------------------------------------- #
        breakdown = {
            "overall_sentiment": aggregate["overall_score"],
            "distribution": aggregate["distribution"],
            "category_scores": aggregate["category_scores"],
        }

        return SentimentScore(
            total=total,
            news_sentiment_score=round(news_sentiment, 2),
            event_impact_score=round(event_impact, 2),
            market_attention_score=round(market_attention, 2),
            source_quality_score=round(source_quality, 2),
            breakdown=breakdown,
            articles=scored_articles,
            timeline=timeline,
            category_summary=category_summary,
        )

    # ------------------------------------------------------------------ #
    # Sub-score calculators
    # ------------------------------------------------------------------ #

    @staticmethod
    def _calc_news_sentiment(overall_score: float) -> float:
        """Map overall_score [-1, 1] -> news_sentiment_score [0, 40]."""
        if overall_score >= 0.5:
            # 35 – 40
            return 35.0 + (overall_score - 0.5) / 0.5 * 5.0
        elif overall_score >= 0.2:
            # 25 – 35
            return 25.0 + (overall_score - 0.2) / 0.3 * 10.0
        elif overall_score >= -0.2:
            # 15 – 25
            return 15.0 + (overall_score + 0.2) / 0.4 * 10.0
        elif overall_score >= -0.5:
            # 5 – 15
            return 5.0 + (overall_score + 0.5) / 0.3 * 10.0
        else:
            # 0 – 5
            return max(0.0, 5.0 + (overall_score + 0.5) / 0.5 * 5.0)

    @staticmethod
    def _calc_event_impact(
        scored_articles: list[dict],
        category_scores: dict[str, float],
    ) -> float:
        """Compute event impact score (0-30) based on high-impact categories."""
        high_impact_cats = {CATEGORY_EARNINGS, CATEGORY_INSIDER, CATEGORY_POLICY}

        # Check whether any high-impact category has a strong score
        max_abs_high = 0.0
        has_high_impact = False
        for cat in high_impact_cats:
            if cat in category_scores:
                has_high_impact = True
                max_abs_high = max(max_abs_high, abs(category_scores[cat]))

        if has_high_impact and max_abs_high >= 0.3:
            # Strong high-impact event: 25-30
            return 25.0 + min(max_abs_high, 1.0) * 5.0
        elif has_high_impact and max_abs_high >= 0.1:
            # Moderate high-impact event: 15-25
            return 15.0 + (max_abs_high / 0.3) * 10.0
        elif has_high_impact:
            # Present but weak: 10-15
            return 10.0 + max_abs_high / 0.1 * 5.0
        else:
            # No significant events — base on general article strength
            if scored_articles:
                avg_abs = sum(abs(a["score"]) for a in scored_articles) / len(
                    scored_articles
                )
                return 10.0 + min(avg_abs, 0.5) * 10.0
            return 10.0

    @staticmethod
    def _calc_market_attention(article_count: int, overall_score: float) -> float:
        """Compute market attention score (0-15) based on article volume."""
        if article_count > 15:
            base = 12.0
        elif article_count >= 8:
            base = 8.0 + (article_count - 8) / 7.0 * 2.0
        else:
            base = 5.0 + max(0, article_count - 1) / 7.0 * 2.0

        # Bonus for high attention combined with positive sentiment
        if article_count > 15 and overall_score > 0.2:
            base = min(15.0, base + 2.0)

        return min(15.0, base)

    @staticmethod
    def _calc_source_quality(scored_articles: list[dict]) -> float:
        """Compute source quality score (0-15) based on average source quality."""
        if not scored_articles:
            return 5.0

        avg_quality = sum(
            a.get("source_quality", 0.5) for a in scored_articles
        ) / len(scored_articles)

        if avg_quality >= 0.9:
            # Mostly tier-1: 13-15
            return 13.0 + (avg_quality - 0.9) / 0.1 * 2.0
        elif avg_quality >= 0.6:
            # Mixed: 8-13
            return 8.0 + (avg_quality - 0.6) / 0.3 * 5.0
        else:
            # Mostly unknown: 5-8
            return 5.0 + (avg_quality / 0.6) * 3.0

    # ------------------------------------------------------------------ #
    # Builders
    # ------------------------------------------------------------------ #

    @staticmethod
    def _build_timeline(scored_articles: list[dict]) -> list[dict]:
        """Build a timeline of articles sorted by date with color coding."""
        timeline: list[dict] = []
        for article in scored_articles:
            score = article.get("score", 0.0)
            if score > 0.1:
                color = "green"
            elif score < -0.1:
                color = "red"
            else:
                color = "gray"

            timeline.append({
                "title": article.get("title", ""),
                "url": article.get("url", ""),
                "date": article.get("published_date", ""),
                "score": score,
                "color": color,
                "category": article.get("category", "general"),
            })

        # Sort by date descending (most recent first); undated articles last
        timeline.sort(key=lambda x: x.get("date") or "", reverse=True)
        return timeline

    @staticmethod
    def _build_category_summary(scored_articles: list[dict]) -> dict:
        """Build per-category summary: count, avg_score, impact label."""
        buckets: dict[str, list[float]] = {}
        for article in scored_articles:
            cat = article.get("category", "general")
            buckets.setdefault(cat, []).append(article["score"])

        summary: dict[str, dict] = {}
        for cat, scores in buckets.items():
            avg = sum(scores) / len(scores) if scores else 0.0
            abs_avg = abs(avg)
            if abs_avg >= 0.3:
                impact = "high"
            elif abs_avg >= 0.1:
                impact = "medium"
            else:
                impact = "low"

            summary[cat] = {
                "count": len(scores),
                "avg_score": round(avg, 4),
                "impact": impact,
            }

        return summary
