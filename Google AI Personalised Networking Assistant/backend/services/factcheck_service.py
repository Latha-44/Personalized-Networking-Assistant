"""
factcheck_service.py
----------------------
Quick fact verification backed by the public Wikipedia REST API (no API key
required). We call the API directly with `requests` rather than the
`wikipedia` PyPI package so behavior is fully transparent and easy to debug.
"""

from typing import Optional
import requests

WIKI_SEARCH_URL = "https://en.wikipedia.org/w/api.php"
WIKI_SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"

HEADERS = {"User-Agent": "PersonalizedNetworkingAssistant/1.0 (educational project)"}


def _search_best_title(query: str) -> Optional[str]:
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "format": "json",
        "srlimit": 1,
    }
    resp = requests.get(WIKI_SEARCH_URL, params=params, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    results = data.get("query", {}).get("search", [])
    if not results:
        return None
    return results[0]["title"]


def fact_check(query: str) -> dict:
    """Look up `query` on Wikipedia and return a short summary + source URL.

    Returns a dict shaped like:
        {"query": str, "summary": str, "source_url": str | None, "found": bool}
    """
    try:
        title = _search_best_title(query)
        if not title:
            return {
                "query": query,
                "summary": "No relevant Wikipedia article was found for this query.",
                "source_url": None,
                "found": False,
            }

        resp = requests.get(
            WIKI_SUMMARY_URL.format(title=title.replace(" ", "_")),
            headers=HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        summary_data = resp.json()

        return {
            "query": query,
            "summary": summary_data.get("extract", "No summary available."),
            "source_url": summary_data.get("content_urls", {}).get("desktop", {}).get("page"),
            "found": True,
        }
    except requests.RequestException as exc:
        return {
            "query": query,
            "summary": f"Fact-check service is temporarily unavailable ({exc}).",
            "source_url": None,
            "found": False,
        }
