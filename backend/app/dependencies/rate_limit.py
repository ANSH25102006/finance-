import time
import logging
from collections import defaultdict
from typing import Dict, List
from fastapi import Request, HTTPException, status
from app.core.security import decode_access_token

logger = logging.getLogger("rate_limiter")

# In-memory store for tracking timestamps of requests per client
# Key: (client_id, endpoint_path)
# Value: List of timestamps (floats) representing recent requests
_request_history: Dict[tuple, List[float]] = defaultdict(list)


class RateLimiter:
    """
    Sliding window in-memory rate limiter.
    Limits requests to a given threshold inside a defined temporal window.
    Evaluates JWT 'sub' claim if authenticated; otherwise falls back to client IP.
    """
    def __init__(self, requests_limit: int, window_seconds: int):
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds

    def __call__(self, request: Request):
        client_id = "anonymous"
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                token = auth_header.split(" ")[1]
                payload = decode_access_token(token)
                if payload and "sub" in payload:
                    client_id = payload["sub"]
            except Exception as e:
                logger.debug(f"Failed to decode token for rate limiting identifier: {e}")
                pass

        if client_id == "anonymous":
            client_id = request.client.host if request.client else "unknown"

        endpoint = request.url.path
        now = time.time()
        key = (client_id, endpoint)

        # Retrieve request timestamps and clean up expired ones
        timestamps = _request_history[key]
        timestamps = [t for t in timestamps if now - t < self.window_seconds]

        if len(timestamps) >= self.requests_limit:
            # Calculate remaining cooldown time based on the oldest timestamp in window
            oldest_timestamp = timestamps[0]
            retry_after = int(self.window_seconds - (now - oldest_timestamp))
            retry_after = max(retry_after, 1)

            logger.warning(
                f"Rate limit exceeded for client {client_id} on {endpoint}. "
                f"Limit: {self.requests_limit}/{self.window_seconds}s. Blocked."
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later.",
                headers={"Retry-After": str(retry_after)}
            )

        # Record this request
        timestamps.append(now)
        _request_history[key] = timestamps
