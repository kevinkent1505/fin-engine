from email.utils import parsedate_to_datetime
import time

import httpx


class PoliteHttpClient:
    """
    Sequential HTTP client with a hard minimum delay and conservative retry.

    It intentionally does not implement proxy rotation, fingerprint evasion,
    CAPTCHA handling, or parallel requests.
    """

    def __init__(
        self,
        *,
        delay_seconds: float = 2.0,
        timeout_seconds: float = 30.0,
        max_retries: int = 3,
        user_agent: str = "FinEngine/0.1 authorized-marketplace-crawler",
    ) -> None:
        if delay_seconds < 1.0:
            raise ValueError("delay_seconds must be at least 1.0")

        self.delay_seconds = delay_seconds
        self.max_retries = max_retries
        self._last_request_at: float | None = None
        self._client = httpx.Client(
            follow_redirects=True,
            timeout=timeout_seconds,
            headers={
                "User-Agent": user_agent,
                "Accept": "text/html,application/xhtml+xml",
            },
        )

    def __enter__(self) -> "PoliteHttpClient":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self._client.close()

    def get(self, url: str) -> httpx.Response:
        for attempt in range(self.max_retries + 1):
            self._wait_for_slot()
            response = self._client.get(url)
            self._last_request_at = time.monotonic()

            if response.status_code not in {429, 503}:
                response.raise_for_status()
                return response

            if attempt >= self.max_retries:
                response.raise_for_status()

            time.sleep(self._retry_delay(response, attempt))

        raise RuntimeError("unreachable")

    def _wait_for_slot(self) -> None:
        if self._last_request_at is None:
            return

        elapsed = time.monotonic() - self._last_request_at
        remaining = self.delay_seconds - elapsed
        if remaining > 0:
            time.sleep(remaining)

    def _retry_delay(
        self,
        response: httpx.Response,
        attempt: int,
    ) -> float:
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            parsed = self._parse_retry_after(retry_after)
            if parsed is not None:
                return min(max(parsed, self.delay_seconds), 120.0)

        return min(self.delay_seconds * (2 ** (attempt + 1)), 60.0)

    @staticmethod
    def _parse_retry_after(value: str) -> float | None:
        value = value.strip()
        if value.isdigit():
            return float(value)

        try:
            target = parsedate_to_datetime(value)
        except (TypeError, ValueError):
            return None

        now = parsedate_to_datetime(
            time.strftime(
                "%a, %d %b %Y %H:%M:%S GMT",
                time.gmtime(),
            )
        )
        return max((target - now).total_seconds(), 0.0)
