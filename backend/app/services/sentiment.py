"""
Sentiment analysis service.

Fetches news via NewsProviderManager (Tavily / Brave / DuckDuckGo with failover),
scores articles with keyword-based SentimentScorer (or optional AI scoring),
and produces a composite SentimentScore.
"""

from __future__ import annotations

import logging
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
# NewsFetcher — delegates to NewsProviderManager
# ---------------------------------------------------------------------------

class NewsFetcher:
    """Fetch news articles using multi-source NewsProviderManager."""

    def __init__(self) -> None:
        from app.services.news_providers import NewsProviderManager
        self._manager = NewsProviderManager()

    async def fetch_news(
        self,
        code: str,
        name: str,
        market: str,
    ) -> list[dict]:
        """Fetch recent news articles for the given stock.

        Returns list[dict] with keys: title, content, url, published_date, source.
        """
        queries = self._build_queries(code, name, market)
        articles = await self._manager.search_multiple(queries, max_results_per_query=5)

        # Convert NewsArticle dataclasses to dicts for backward compatibility
        return [
            {
                "title": a.title,
                "content": a.content,
                "url": a.url,
                "published_date": a.published_date,
                "source": a.source,
            }
            for a in articles
        ]

    @staticmethod
    def _build_queries(code: str, name: str, market: str) -> list[str]:
        """Build expanded search queries tailored to the market."""
        market_upper = market.upper()

        if market_upper == "CN":
            return [
                f"{name} 最新消息",
                f"{name} 研报 分析 评级",
                f"{code} 风险 公告 减持",
                f"{name} 业绩 营收 利润",
                f"{name} 行业 竞争 前景",
            ]
        elif market_upper == "HK":
            return [
                f"{name} stock news Hong Kong",
                f"{code}.HK analyst rating",
                f"{name} earnings revenue",
            ]
        else:
            # US-style queries
            return [
                f"{code} {name} stock news",
                f"{code} earnings analyst rating",
                f"{code} risk litigation insider",
                f"{code} revenue growth forecast",
                f"{code} industry outlook",
            ]


# ---------------------------------------------------------------------------
# AI-based sentiment scoring (optional)
# ---------------------------------------------------------------------------

async def _ai_score_articles(articles: list[dict]) -> list[dict] | None:
    """Attempt to score articles using an AI provider.

    Batch-sends article titles to LLM for +1/0/-1 classification.
    Returns scored articles or None if AI is unavailable.
    """
    if not articles:
        return None

    try:
        from app.services.ai_provider import get_ai_provider
        provider = get_ai_provider()
    except Exception:
        return None

    titles = [a.get("title", "") for a in articles[:20]]
    numbered = "\n".join(f"{i+1}. {t}" for i, t in enumerate(titles) if t)
    if not numbered:
        return None

    prompt = (
        "Classify each headline's financial sentiment as +1 (positive), "
        "0 (neutral), or -1 (negative). Respond ONLY with a JSON array "
        "of integers, e.g. [1, 0, -1, ...]. No other text.\n\n"
        f"Headlines:\n{numbered}"
    )

    try:
        import json
        raw = await provider.generate(prompt=prompt, system_prompt="You are a financial sentiment classifier.")
        # Parse the response
        raw = raw.strip()
        if raw.startswith("["):
            scores = json.loads(raw)
        else:
            import re
            match = re.search(r"\[[\s\S]*?\]", raw)
            if match:
                scores = json.loads(match.group(0))
            else:
                return None

        if not isinstance(scores, list) or len(scores) < len(titles):
            return None

        # Apply AI scores to articles
        scored = []
        for i, article in enumerate(articles[:20]):
            s = scores[i] if i < len(scores) else 0
            s = max(-1, min(1, int(s)))
            scored.append({
                **article,
                "score": float(s),
                "ai_scored": True,
            })

        # Include remaining articles (beyond 20) with score 0
        for article in articles[20:]:
            scored.append({**article, "score": 0.0, "ai_scored": False})

        return scored
    except Exception:
        logger.debug("AI sentiment scoring failed, falling back to keywords", exc_info=True)
        return None


# ---------------------------------------------------------------------------
# SentimentService
# ---------------------------------------------------------------------------

class SentimentService:
    """Orchestrates news fetching and sentiment scoring."""

    def __init__(self) -> None:
        self._fetcher = NewsFetcher()
        self._scorer = SentimentScorer()

    async def analyze(self, stock_data: Any) -> SentimentScore:
        """Run full sentiment analysis for a stock."""
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
        # Try AI scoring first, fall back to keyword scoring
        ai_scored = await _ai_score_articles(articles)
        if ai_scored is not None:
            scored_articles = ai_scored
            logger.info("Using AI-based sentiment scoring for %d articles", len(scored_articles))
        else:
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
            return 35.0 + (overall_score - 0.5) / 0.5 * 5.0
        elif overall_score >= 0.2:
            return 25.0 + (overall_score - 0.2) / 0.3 * 10.0
        elif overall_score >= -0.2:
            return 15.0 + (overall_score + 0.2) / 0.4 * 10.0
        elif overall_score >= -0.5:
            return 5.0 + (overall_score + 0.5) / 0.3 * 10.0
        else:
            return max(0.0, 5.0 + (overall_score + 0.5) / 0.5 * 5.0)

    @staticmethod
    def _calc_event_impact(
        scored_articles: list[dict],
        category_scores: dict[str, float],
    ) -> float:
        """Compute event impact score (0-30) based on high-impact categories."""
        high_impact_cats = {CATEGORY_EARNINGS, CATEGORY_INSIDER, CATEGORY_POLICY}

        max_abs_high = 0.0
        has_high_impact = False
        for cat in high_impact_cats:
            if cat in category_scores:
                has_high_impact = True
                max_abs_high = max(max_abs_high, abs(category_scores[cat]))

        if has_high_impact and max_abs_high >= 0.3:
            return 25.0 + min(max_abs_high, 1.0) * 5.0
        elif has_high_impact and max_abs_high >= 0.1:
            return 15.0 + (max_abs_high / 0.3) * 10.0
        elif has_high_impact:
            return 10.0 + max_abs_high / 0.1 * 5.0
        else:
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
            return 13.0 + (avg_quality - 0.9) / 0.1 * 2.0
        elif avg_quality >= 0.6:
            return 8.0 + (avg_quality - 0.6) / 0.3 * 5.0
        else:
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
