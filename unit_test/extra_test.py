import time
import urllib.error
import urllib.request
from email.message import Message
from typing import Any

import pytest

from cibuildwheel import extra


def test_github_api_request_waits_for_rate_limit_reset(monkeypatch: pytest.MonkeyPatch) -> None:
    headers = Message()
    headers["x-ratelimit-remaining"] = "0"
    headers["x-ratelimit-reset"] = str(int(time.time()) + 42)
    headers["date"] = "Wed, 23 Sep 2026 16:01:43 GMT"
    urls: list[str] = []
    sleeps: list[float] = []

    def fake_json_request(request: urllib.request.Request) -> dict[str, Any]:
        urls.append(request.full_url)
        if len(urls) == 1:
            raise urllib.error.HTTPError(request.full_url, 403, "rate limit exceeded", headers, None)
        return {"tag_name": "v1"}

    monkeypatch.setattr(extra, "_json_request", fake_json_request)
    monkeypatch.setattr(time, "sleep", sleeps.append)

    assert extra.github_api_request("repos/pypa/cibuildwheel/releases/latest") == {"tag_name": "v1"}
    assert urls == ["https://api.github.com/repos/pypa/cibuildwheel/releases/latest"] * 2
    assert 40 <= sleeps[0] <= 42
