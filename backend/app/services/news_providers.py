"""
News provider abstraction with multi-source failover.

Supports Tavily, Brave Search, and DuckDuckGo as news sources.
Providers are tried in priority order; if one fails, the next is attempted.
"""
from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class NewsArticle:
    """Normalized news article from any provider."""

    title: str
    content: str
    url: str
    published_date: str = ""
    source: str = ""


class BaseNewsProvider(ABC):
    """Abstract base for news search providers."""

    name: str = "base"
    priority: int = 99

    @abstractmethod
    async def search(self, query: str, max_results: int = 5) -> list[NewsArticle]:
        """Search for news articles matching the query."""
        ...

    def is_available(self) -> bool:
        """Check if this provider is configured and importable."""
        return True


class TavilyNewsProvider(BaseNewsProvider):
    """Tavily search API provider (priority 0)."""

    name = "tavily"
    priority = 0

    def __init__(self, api_key: str):
        self._api_key = api_key
        self._client: Any = None

    def is_available(self) -> bool:
        if not self._api_key:
            return False
        try:
            from tavily import TavilyClient  # type: ignore[import-untyped]
            if self._client is None:
                self._client = TavilyClient(api_key=self._api_key)
            return True
        except ImportError:
            return False

    async def search(self, query: str, max_results: int = 5) -> list[NewsArticle]:
        if not self.is_available():
            return []

        results = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self._client.search(
                query=query,
                max_results=max_results,
                include_answer=False,
            ),
        )

        articles = []
        for item in results.get("results", []):
            articles.append(NewsArticle(
                title=item.get("title", ""),
                content=item.get("content", ""),
                url=item.get("url", ""),
                published_date=item.get("published_date", ""),
                source=item.get("source", ""),
            ))
        return articles


class BraveNewsProvider(BaseNewsProvider):
    """Brave Search API provider (priority 1)."""

    name = "brave"
    priority = 1

    def __init__(self, api_key: str):
        self._api_key = api_key

    def is_available(self) -> bool:
        return bool(self._api_key)

    async def search(self, query: str, max_results: int = 5) -> list[NewsArticle]:
        if not self._api_key:
            return []

        import urllib.request
        import urllib.parse
        import json

        url = (
            "https://api.search.brave.com/res/v1/news/search?"
            + urllib.parse.urlencode({"q": query, "count": max_results})
        )
        req = urllib.request.Request(url, headers={
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self._api_key,
        })

        def _do_request():
            import gzip
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = resp.read()
                if resp.headers.get("Content-Encoding") == "gzip":
                    data = gzip.decompress(data)
                return json.loads(data)

        result = await asyncio.get_event_loop().run_in_executor(None, _do_request)

        articles = []
        for item in result.get("results", []):
            articles.append(NewsArticle(
                title=item.get("title", ""),
                content=item.get("description", ""),
                url=item.get("url", ""),
                published_date=item.get("age", ""),
                source=item.get("meta_url", {}).get("hostname", "") if isinstance(item.get("meta_url"), dict) else "",
            ))
        return articles


class DuckDuckGoNewsProvider(BaseNewsProvider):
    """DuckDuckGo news search provider (priority 2, free, no API key)."""

    name = "duckduckgo"
    priority = 2

    def is_available(self) -> bool:
        try:
            from duckduckgo_search import DDGS  # type: ignore[import-untyped]
            return True
        except ImportError:
            return False

    async def search(self, query: str, max_results: int = 5) -> list[NewsArticle]:
        try:
            from duckduckgo_search import DDGS  # type: ignore[import-untyped]
        except ImportError:
            logger.debug("duckduckgo-search not installed, skipping DDG provider")
            return []

        def _do_search():
            with DDGS() as ddgs:
                return list(ddgs.news(query, max_results=max_results))

        results = await asyncio.get_event_loop().run_in_executor(None, _do_search)

        articles = []
        for item in results:
            articles.append(NewsArticle(
                title=item.get("title", ""),
                content=item.get("body", ""),
                url=item.get("url", ""),
                published_date=item.get("date", ""),
                source=item.get("source", ""),
            ))
        return articles


class NewsProviderManager:
    """Manages multiple news providers with failover.

    Tries providers in priority order (lowest number first).
    Falls back to the next provider if one fails.
    """

    def __init__(self):
        from app.config import settings

        self._providers: list[BaseNewsProvider] = []

        # Add providers in priority order
        tavily_key = getattr(settings, "tavily_api_key", "") or ""
        if tavily_key:
            self._providers.append(TavilyNewsProvider(api_key=tavily_key))

        brave_key = getattr(settings, "brave_api_key", "") or ""
        if brave_key:
            self._providers.append(BraveNewsProvider(api_key=brave_key))

        # DuckDuckGo is always added (free, no key needed)
        self._providers.append(DuckDuckGoNewsProvider())

        # Sort by priority
        self._providers.sort(key=lambda p: p.priority)

        available = [p.name for p in self._providers if p.is_available()]
        logger.info("NewsProviderManager initialized — available: %s", available)

    async def search(self, query: str, max_results: int = 5) -> list[NewsArticle]:
        """Search using the first available provider, with failover."""
        for provider in self._providers:
            if not provider.is_available():
                continue
            try:
                articles = await provider.search(query, max_results=max_results)
                if articles:
                    logger.debug(
                        "News provider '%s' returned %d results for query: %s",
                        provider.name, len(articles), query,
                    )
                    return articles
            except Exception:
                logger.warning(
                    "News provider '%s' failed for query: %s",
                    provider.name, query, exc_info=True,
                )
                continue

        logger.warning("All news providers failed for query: %s", query)
        return []

    async def search_multiple(
        self, queries: list[str], max_results_per_query: int = 5
    ) -> list[NewsArticle]:
        """Search multiple queries and deduplicate by URL."""
        all_articles: list[NewsArticle] = []
        seen_urls: set[str] = set()

        for query in queries:
            try:
                articles = await self.search(query, max_results=max_results_per_query)
                for article in articles:
                    if article.url and article.url not in seen_urls:
                        seen_urls.add(article.url)
                        all_articles.append(article)
            except Exception:
                logger.exception("search_multiple failed for query: %s", query)

        return all_articles
