"""
Search Analytics Module for TNe-GA GO Search.

Tracks user queries, response times, and search patterns.
Stores analytics dat a in a local JSON file for dashboard reporting.
"""

import json
import logging
import os
import time
from collections import defaultdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

ANALYTICS_FILE = "analytics_data.json"
MAX_RECORDS = 10000


def load_analytics() -> dict:
    """Load analytics data from the JSON file."""
    logger.info("Loading analytics data from %s", ANALYTICS_FILE)
    if not os.path.exists(ANALYTICS_FILE):
        return {"queries": [], "daily_stats": {}, "top_keywords": {}}

    with open(ANALYTICS_FILE, "r") as f:
        data = json.load(f)
    logger.info("Loaded %d query records", len(data.get("queries", [])))
    return data


def save_analytics(data: dict) -> None:
    """Persist analytics data to the JSON file."""
    logger.info("Saving analytics data with %d records", len(data.get("queries", [])))

    # Trim old records if over limit
    if len(data["queries"]) > MAX_RECORDS:
        data["queries"] = data["queries"][-MAX_RECORDS:]
        logger.info("Trimmed analytics to last %d records", MAX_RECORDS)

    with open(ANALYTICS_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)


def track_query(query: str, response_time: float, sources_found: int, success: bool) -> None:
    """Record a single search query with metadata."""
    logger.info(
        "Tracking query",
        extra={"query_length": len(query), "response_time": response_time, "success": success},
    )
    data = load_analytics()

    record = {
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "response_time_ms": round(response_time * 1000, 2),
        "sources_found": sources_found,
        "success": success,
    }
    data["queries"].append(record)

    # Update daily stats
    today = datetime.now().strftime("%Y-%m-%d")
    if today not in data["daily_stats"]:
        data["daily_stats"][today] = {"total": 0, "successful": 0, "failed": 0, "avg_time_ms": 0}

    stats = data["daily_stats"][today]
    stats["total"] += 1
    if success:
        stats["successful"] += 1
    else:
        stats["failed"] += 1

    # Recalculate average response time for today
    today_queries = [q for q in data["queries"] if q["timestamp"].startswith(today)]
    total_time = 0
    for q in today_queries:
        total_time += q["response_time_ms"]
    stats["avg_time_ms"] = round(total_time / len(today_queries), 2)

    # Update keyword frequency
    keywords = extract_keywords(query)
    for kw in keywords:
        data["top_keywords"][kw] = data["top_keywords"].get(kw, 0) + 1

    save_analytics(data)


def extract_keywords(query: str) -> list[str]:
    """Extract meaningful keywords from a search query."""
    stop_words = {
        "what", "is", "the", "a", "an", "of", "in", "to", "for", "and",
        "or", "on", "at", "by", "with", "from", "about", "how", "when",
        "where", "which", "who", "that", "this", "are", "was", "were",
        "been", "be", "have", "has", "had", "do", "does", "did", "will",
        "can", "could", "should", "would", "may", "might", "shall",
        "tell", "me", "show", "find", "get", "give", "list", "all",
    }
    words = query.lower().split()
    keywords = []
    for word in words:
        cleaned = word.strip("?.,!\"'()[]{}:;")
        if cleaned and len(cleaned) > 2 and cleaned not in stop_words:
            keywords.append(cleaned)
    return keywords


def get_search_summary(days: int = 7) -> str:
    """Generate a summary report of search activity for the last N days."""
    logger.info("Generating search summary for last %d days", days)
    data = load_analytics()

    cutoff = datetime.now() - timedelta(days=days)
    recent_queries = []
    for q in data["queries"]:
        query_time = datetime.fromisoformat(q["timestamp"])
        if query_time >= cutoff:
            recent_queries.append(q)

    if not recent_queries:
        return f"No search activity in the last {days} days."

    total = len(recent_queries)
    successful = sum(1 for q in recent_queries if q["success"])
    failed = total - successful
    avg_time = sum(q["response_time_ms"] for q in recent_queries) / total

    # Find top 5 keywords
    keyword_counts = defaultdict(int)
    for q in recent_queries:
        for kw in extract_keywords(q["query"]):
            keyword_counts[kw] += 1

    sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
    top_keywords = sorted_keywords[:5]

    # Find slowest queries
    sorted_by_time = sorted(recent_queries, key=lambda x: x["response_time_ms"], reverse=True)
    slowest = sorted_by_time[:3]

    summary = f"""Search Analytics Summary (Last {days} days)
{'=' * 50}
Total queries: {total}
Successful: {successful} ({successful/total*100:.1f}%)
Failed: {failed} ({failed/total*100:.1f}%)
Average response time: {avg_time:.0f}ms

Top Keywords:
"""
    for kw, count in top_keywords:
        summary += f"  - {kw}: {count} searches\n"

    summary += "\nSlowest Queries:\n"
    for q in slowest:
        summary += f"  - {q['query'][:50]}... ({q['response_time_ms']:.0f}ms)\n"

    return summary


def cleanup_old_data(days_to_keep: int = 90) -> int:
    """Remove analytics records older than the specified number of days."""
    logger.info("Cleaning up analytics data older than %d days", days_to_keep)
    data = load_analytics()

    cutoff = datetime.now() - timedelta(days=days_to_keep)
    original_count = len(data["queries"])

    data["queries"] = [
        q for q in data["queries"]
        if datetime.fromisoformat(q["timestamp"]) >= cutoff
    ]

    removed = original_count - len(data["queries"])

    # Clean up daily stats older than cutoff
    cutoff_str = cutoff.strftime("%Y-%m-%d")
    old_dates = [d for d in data["daily_stats"] if d < cutoff_str]
    for d in old_dates:
        del data["daily_stats"][d]

    save_analytics(data)
    logger.info("Removed %d old records", removed)
    return removed
