"""
Sentiment scoring module for news articles.

Pure computation — no I/O, no AI calls. Scores articles using keyword-based
lexicon analysis with support for English and Chinese text.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# Keyword lexicons
# ---------------------------------------------------------------------------

POSITIVE_EN: list[str] = [
    "beat", "beats", "exceeded", "upgrade", "upgraded", "outperform",
    "buy", "bullish", "growth", "record", "surge", "surged", "rally",
    "breakthrough", "innovation", "profit", "dividend", "acquisition",
    "expansion", "partnership", "strong", "robust", "accelerat",
    "momentum", "optimistic", "upside",
]

NEGATIVE_EN: list[str] = [
    "miss", "missed", "downgrade", "downgraded", "underperform",
    "sell", "bearish", "decline", "loss", "layoff", "lawsuit",
    "investigation", "warning", "risk", "debt", "bankruptcy", "fraud",
    "recall", "weak", "slowdown", "pessimistic", "headwind", "concern",
    "cut", "slash",
]

POSITIVE_CN: list[str] = [
    "利好", "上涨", "增长", "突破", "创新高", "买入", "增持", "超预期",
    "业绩大增", "净利润增", "营收增", "分红", "回购", "扩张", "合作",
    "中标", "获批", "强劲", "加速", "景气", "龙头", "优质",
]

NEGATIVE_CN: list[str] = [
    "利空", "下跌", "亏损", "暴跌", "减持", "卖出", "低于预期",
    "业绩下滑", "营收下降", "违规", "处罚", "诉讼", "退市", "质押",
    "爆仓", "商誉减值", "坏账", "风险", "警示", "负面", "压力", "疲软",
]

# ---------------------------------------------------------------------------
# Article categories
# ---------------------------------------------------------------------------

CATEGORY_EARNINGS = "earnings"
CATEGORY_POLICY = "policy"
CATEGORY_INSIDER = "insider"
CATEGORY_ANALYST = "analyst"
CATEGORY_PRODUCT = "product"
CATEGORY_RISK = "risk"
CATEGORY_MACRO = "macro"
CATEGORY_GENERAL = "general"

ALL_CATEGORIES: list[str] = [
    CATEGORY_EARNINGS,
    CATEGORY_POLICY,
    CATEGORY_INSIDER,
    CATEGORY_ANALYST,
    CATEGORY_PRODUCT,
    CATEGORY_RISK,
    CATEGORY_MACRO,
    CATEGORY_GENERAL,
]

# Keywords that map to each category (checked against the combined text).
_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    CATEGORY_EARNINGS: [
        "earnings", "profit", "revenue", "业绩", "营收",
    ],
    CATEGORY_POLICY: [
        "policy", "regulation", "政策", "监管",
    ],
    CATEGORY_INSIDER: [
        "insider", "buyback", "减持", "增持", "回购",
    ],
    CATEGORY_ANALYST: [
        "analyst", "rating", "target", "研报", "评级",
    ],
    CATEGORY_PRODUCT: [
        "product", "launch", "release", "新品", "发布",
    ],
    CATEGORY_RISK: [
        "lawsuit", "fraud", "investigation", "诉讼", "违规",
    ],
    CATEGORY_MACRO: [
        "gdp", "interest rate", "inflation", "央行", "加息",
    ],
}

# ---------------------------------------------------------------------------
# Source quality tiers
# ---------------------------------------------------------------------------

_TIER1_DOMAINS: set[str] = {
    "reuters.com",
    "bloomberg.com",
    "wsj.com",
    "ft.com",
    "cnbc.com",
    "finance.sina.com.cn",
    "sina.com.cn",
    "eastmoney.com",
}

_TIER2_DOMAINS: set[str] = {
    "marketwatch.com",
    "seekingalpha.com",
    "barrons.com",
    "investing.com",
    "yahoo.com",
    "finance.yahoo.com",
    "cnn.com",
    "bbc.com",
    "foxbusiness.com",
    "thestreet.com",
    "fool.com",
    "benzinga.com",
    "163.com",
    "qq.com",
    "sohu.com",
    "10jqka.com.cn",
    "cls.cn",
    "caixin.com",
    "yicai.com",
    "stcn.com",
    "hexun.com",
}


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _count_keyword_matches(text: str, keywords: list[str]) -> list[str]:
    """Return a list of keywords that appear in *text* (case-insensitive for
    English; exact substring match for Chinese)."""
    text_lower = text.lower()
    matches: list[str] = []
    for kw in keywords:
        # For English keywords we do a word-boundary-ish search so that
        # "accelerat" also matches "accelerating" / "acceleration".
        if re.search(re.escape(kw.lower()), text_lower):
            matches.append(kw)
    return matches


def _extract_domain(url: str) -> str:
    """Return the base domain from a URL (e.g. 'www.reuters.com' -> 'reuters.com')."""
    try:
        host = urlparse(url).hostname or ""
    except Exception:
        return ""
    # Strip leading 'www.'
    if host.startswith("www."):
        host = host[4:]
    return host.lower()


def _assess_source_quality(url: str) -> float:
    """Return a quality multiplier for the article source."""
    domain = _extract_domain(url)
    if not domain:
        return 0.5

    # Check tier-1
    for t1 in _TIER1_DOMAINS:
        if domain == t1 or domain.endswith("." + t1):
            return 1.0

    # Check tier-2
    for t2 in _TIER2_DOMAINS:
        if domain == t2 or domain.endswith("." + t2):
            return 0.7

    return 0.5


def _classify_category(text: str) -> str:
    """Classify an article into a category based on keyword presence."""
    text_lower = text.lower()
    best_category = CATEGORY_GENERAL
    best_count = 0

    for category, keywords in _CATEGORY_KEYWORDS.items():
        count = sum(1 for kw in keywords if kw.lower() in text_lower)
        if count > best_count:
            best_count = count
            best_category = category

    return best_category


# ---------------------------------------------------------------------------
# SentimentScorer
# ---------------------------------------------------------------------------

class SentimentScorer:
    """Score news articles using keyword-based sentiment analysis."""

    def score_article(
        self,
        title: str,
        content: str,
        url: str = "",
    ) -> dict:
        """Score a single article and return a result dict.

        The title is weighted 2x relative to the content.  The final score is
        in the range ``[-1.0, 1.0]``.

        Returns
        -------
        dict
            Keys: title, url, score, category, source_quality,
            positive_matches, negative_matches
        """
        # Build a combined text blob where the title counts double.
        combined = f"{title} {title} {content}"

        # --- Positive matches ---
        pos_en = _count_keyword_matches(combined, POSITIVE_EN)
        pos_cn = _count_keyword_matches(combined, POSITIVE_CN)
        positive_matches = list(set(pos_en + pos_cn))

        # --- Negative matches ---
        neg_en = _count_keyword_matches(combined, NEGATIVE_EN)
        neg_cn = _count_keyword_matches(combined, NEGATIVE_CN)
        negative_matches = list(set(neg_en + neg_cn))

        positive_count = len(positive_matches)
        negative_count = len(negative_matches)

        # Score in [-1, 1]
        score = (positive_count - negative_count) / (positive_count + negative_count + 1)

        # Category
        category = _classify_category(combined)

        # Source quality
        source_quality = _assess_source_quality(url)

        return {
            "title": title,
            "url": url,
            "score": round(score, 4),
            "category": category,
            "source_quality": source_quality,
            "positive_matches": sorted(positive_matches),
            "negative_matches": sorted(negative_matches),
        }

    def score_batch(self, articles: list[dict]) -> list[dict]:
        """Score a list of articles and return them sorted by absolute score
        (descending — most impactful first).

        Each element of *articles* should have at least ``title`` and
        ``content`` keys.  ``url`` is optional.
        """
        scored: list[dict] = []
        for article in articles:
            result = self.score_article(
                title=article.get("title", ""),
                content=article.get("content", ""),
                url=article.get("url", ""),
            )
            # Carry forward any extra keys from the original article
            for key in ("published_date", "source"):
                if key in article:
                    result[key] = article[key]
            scored.append(result)

        scored.sort(key=lambda a: abs(a["score"]), reverse=True)
        return scored

    def compute_aggregate(self, scored_articles: list[dict]) -> dict:
        """Compute aggregate sentiment metrics across a list of scored
        articles.

        Returns
        -------
        dict
            Keys: overall_score, category_scores, distribution, article_count
        """
        if not scored_articles:
            return {
                "overall_score": 0.0,
                "category_scores": {},
                "distribution": {"positive": 0, "neutral": 0, "negative": 0},
                "article_count": 0,
            }

        # --- Weighted average (by source quality) ---
        total_weight = 0.0
        weighted_sum = 0.0
        for article in scored_articles:
            w = article.get("source_quality", 0.5)
            weighted_sum += article["score"] * w
            total_weight += w

        overall_score = weighted_sum / total_weight if total_weight > 0 else 0.0

        # --- Category breakdown ---
        category_sums: dict[str, float] = {}
        category_counts: dict[str, int] = {}
        for article in scored_articles:
            cat = article.get("category", CATEGORY_GENERAL)
            category_sums[cat] = category_sums.get(cat, 0.0) + article["score"]
            category_counts[cat] = category_counts.get(cat, 0) + 1

        category_scores: dict[str, float] = {}
        for cat in category_sums:
            category_scores[cat] = round(
                category_sums[cat] / category_counts[cat], 4
            )

        # --- Distribution ---
        positive = 0
        neutral = 0
        negative = 0
        for article in scored_articles:
            s = article["score"]
            if s > 0.1:
                positive += 1
            elif s < -0.1:
                negative += 1
            else:
                neutral += 1

        return {
            "overall_score": round(overall_score, 4),
            "category_scores": category_scores,
            "distribution": {
                "positive": positive,
                "neutral": neutral,
                "negative": negative,
            },
            "article_count": len(scored_articles),
        }
