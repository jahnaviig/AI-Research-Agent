from __future__ import annotations

from urllib.parse import urlparse

import httpx

from app.models.domain import Source


TRUSTED_DOMAIN_HINTS = {
    ".gov": 0.98,
    ".edu": 0.95,
    "nature.com": 0.94,
    "science.org": 0.94,
    "who.int": 0.96,
    "worldbank.org": 0.94,
    "oecd.org": 0.93,
    "reuters.com": 0.88,
    "apnews.com": 0.88,
}


def score_domain(domain: str) -> float:
    for hint, score in TRUSTED_DOMAIN_HINTS.items():
        if domain.endswith(hint) or hint in domain:
            return score
    if domain.endswith(".org"):
        return 0.78
    if domain.endswith(".com"):
        return 0.68
    return 0.6


class TavilyClient:
    def __init__(self, api_key: str | None, timeout: float = 20.0) -> None:
        self.api_key = api_key
        self.timeout = timeout

    async def search(self, query: str, max_results: int = 5) -> list[Source]:
        if not self.api_key:
            return self._mock_sources(query, max_results)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": self.api_key,
                    "query": query,
                    "search_depth": "advanced",
                    "include_answer": False,
                    "include_raw_content": True,
                    "max_results": max_results,
                },
            )
            response.raise_for_status()
            payload = response.json()

        sources: list[Source] = []
        for index, item in enumerate(payload.get("results", []), start=1):
            url = item.get("url", "")
            domain = urlparse(url).netloc.replace("www.", "")
            sources.append(
                Source(
                    id=index,
                    title=item.get("title") or domain or "Untitled source",
                    url=url,
                    domain=domain,
                    domain_score=score_domain(domain),
                    publish_date=item.get("published_date") or item.get("publishedDate"),
                    content=item.get("raw_content") or item.get("content") or "",
                )
            )
        return sources

    def _mock_sources(self, query: str, max_results: int) -> list[Source]:
        safe_query = query[:90]
        fixtures = [
            ("Research context brief", "https://example.edu/research-context", ".edu"),
            ("Recent market and policy analysis", "https://example.org/analysis", ".org"),
            ("Industry reporting summary", "https://example.com/reporting", ".com"),
        ]
        return [
            Source(
                id=index,
                title=title,
                url=url,
                domain=urlparse(url).netloc,
                domain_score=score_domain(domain),
                publish_date="2026-01-15",
                content=(
                    f"{title} for {safe_query}. The source discusses evidence, limitations, "
                    "reported dates, stakeholder positions, and areas where primary data is sparse."
                ),
            )
            for index, (title, url, domain) in enumerate(fixtures[:max_results], start=1)
        ]

