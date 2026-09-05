"""In-memory event feed pagination."""

import base64
import json


def _encode(timestamp):
    payload = json.dumps({"after": timestamp}).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("ascii")


def _decode(cursor):
    return json.loads(base64.urlsafe_b64decode(cursor))["after"]


def page(events, tenant, status=None, limit=20, cursor=None, reverse=False):
    """Return one page of a tenant's event feed."""
    ordered = sorted(events, key=lambda event: event["created_at"], reverse=reverse)
    if cursor is not None:
        after = _decode(cursor)
        if reverse:
            ordered = [event for event in ordered if event["created_at"] < after]
        else:
            ordered = [event for event in ordered if event["created_at"] > after]

    window = ordered[:limit]
    items = [
        event for event in window
        if event["tenant"] == tenant and (not status or event["status"] == status)
    ]
    next_cursor = None
    if window and len(ordered) > limit:
        next_cursor = _encode(window[-1]["created_at"])
    return {"items": items, "next_cursor": next_cursor}
