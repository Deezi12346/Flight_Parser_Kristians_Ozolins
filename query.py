"""Filter and sort flights using the supplied query conditions."""

import math
from validator import valid_datetime

RECORD_FIELDS = {"flight_id", "origin", "destination", "departure_datetime",
                 "arrival_datetime", "price"}
QUERY_FIELDS = RECORD_FIELDS | {"min_price", "sort_by", "order", "limit"}


def run_query(db: list[dict], query: dict) -> dict:
    """Return the matching flights or an INVALID_QUERY response."""
    invalid = {"query": query, "error": "INVALID_QUERY", "matches": []}

    if not isinstance(query, dict):
        return invalid

    for key, value in query.items():
        if key not in QUERY_FIELDS:
            return invalid

        if key in ("flight_id", "origin", "destination"):
            if not isinstance(value, str):
                return invalid
        elif key in ("departure_datetime", "arrival_datetime"):
            if not isinstance(value, str) or not valid_datetime(value):
                return invalid
        elif key in ("price", "min_price"):
            if type(value) not in (int, float) or (type(value) is float and not math.isfinite(value)):
                return invalid
        elif key == "sort_by":
            if not isinstance(value, str) or value not in RECORD_FIELDS:
                return invalid
        elif key == "order":
            if value not in ("asc", "desc") or not isinstance(value, str):
                return invalid
        elif key == "limit":
            if type(value) is not int or value < 0:
                return invalid

    if "order" in query and "sort_by" not in query:
        return invalid

    matches = []
    for flight in db:
        good = True
        for key, value in query.items():
            if key in ("flight_id", "origin", "destination"):
                if flight[key] != value:
                    good = False
            elif key == "departure_datetime":
                if flight[key] < value:
                    good = False
            elif key == "arrival_datetime":
                if flight[key] > value:
                    good = False
            elif key == "price":
                if flight["price"] > value:
                    good = False
            elif key == "min_price":
                if flight["price"] < value:
                    good = False
        if good:
            matches.append(flight)

    if "sort_by" in query:
        field = query["sort_by"]
        descending = query.get("order", "asc") == "desc"
        matches = sorted(matches, key=lambda flight: flight[field], reverse=descending)

    if "limit" in query:
        matches = matches[:query["limit"]]

    return {"query": query, "matches": matches}


def run_queries(db: list[dict], queries: dict | list) -> list[dict]:
    """Return a response entry for every query, even when a query is invalid."""
    if isinstance(queries, dict):
        queries = [queries]
    return [run_query(db, query) for query in queries]
