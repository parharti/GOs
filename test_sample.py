"""Sample module to test Gemini code review pipeline."""

import logging

logger = logging.getLogger(__name__)


def divide_numbers(a, b):
    logger.info("divide_numbers called", extra={"a": a, "b": b})
    # Bug: no zero division check
    result = a / b
    return result


def find_user(users, target_id):
    # Missing logging
    for i in range(len(users)):
        if users[i]["id"] == target_id:
            return users[i]
    return None


def process_items(items):
    logger.info("process_items called", extra={"count": len(items)})
    results = []
    # Potential O(n^2) nested loop
    for item in items:
        for other in items:
            if item["id"] != other["id"] and item["category"] == other["category"]:
                results.append((item["name"], other["name"]))
    return results


def fetch_data():
    logger.info("fetch_data called")
    # Potential infinite loop - no break condition
    data = []
    while True:
        chunk = get_next_chunk()
        if chunk:
            data.append(chunk)
    return data


def build_query(user_input):
    logger.info("build_query called")
    # SQL injection vulnerability
    query = f"SELECT * FROM users WHERE name = '{user_input}'"
    return query
