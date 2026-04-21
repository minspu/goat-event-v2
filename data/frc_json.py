from __future__ import annotations

import base64
from enum import IntEnum
import json
import os
from pathlib import Path
from typing import Any, cast

from dotenv import load_dotenv
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from utils.data_util import is_json_object


class FRCRequestError(Exception):
    """Base exception for FRC JSON fetch failures."""


class FRCNetworkError(FRCRequestError):
    """Raised when a network-level request error occurs."""


class FRCHTTPError(FRCRequestError):
    """Raised when the server returns a non-2xx response."""


class FRCJSONDecodeError(FRCRequestError):
    """Raised when the response body is not valid JSON."""


class FRCJSONTypeError(FRCRequestError):
    """Raised when the JSON payload is not an object/dict."""


class FRCAuthorizationError(FRCRequestError):
    """Raised when API authorization is missing or malformed."""


class EventRequestType(IntEnum):
    TEAMS = 1
    RANKINGS = 2
    ALLIANCES = 3
    QUALIFICATION_MATCHES = 4
    PLAYOFF_MATCHES = 5
    AWARDS = 6
    QUALIFICATION_SCORE_DETAILS = 7
    PLAYOFF_SCORE_DETAILS = 8


class SeasonRequestType(IntEnum):
    EVENT_LISTING = 1
    TEAM_LISTING = 2


def _cache_root_path() -> Path:
    cacheRootOverride = os.getenv("GOAT_EVENT_CACHE_ROOT")
    if cacheRootOverride and cacheRootOverride.strip():
        return Path(cacheRootOverride).expanduser()
    return Path(__file__).resolve().parents[1] / "cache"


def _cache_file_path(season: int, eventCode: str) -> Path:
    cacheRoot = _cache_root_path()
    seasonStr = str(season)
    return cacheRoot / seasonStr / f"{seasonStr}-{eventCode}.json"


def _bypass_file_path(season: int) -> Path:
    cacheRoot = _cache_root_path()
    seasonStr = str(season)
    return cacheRoot / seasonStr / f"BypassEvents.json"


def _season_cache_file_path(season: int) -> Path:
    cacheRoot = _cache_root_path()
    seasonStr = str(season)
    return cacheRoot / seasonStr / "SeasonData.json"


def bypass_event_cache_file(season: int, eventCode: str) -> None:
    normalizedEventCode = eventCode.strip()
    if not normalizedEventCode:
        raise ValueError("eventCode cannot be empty")

    cachePath = _cache_file_path(season=season, eventCode=normalizedEventCode)
    bypassPath = _bypass_file_path(season=season)

    bypassData = _read_cache_file(bypassPath)
    bypassList = bypassData.get("bypassEvents")
    if not isinstance(bypassList, list):
        bypassList = []
    typedBypassList = cast(list[object], bypassList)

    if normalizedEventCode not in typedBypassList:
        typedBypassList.append(normalizedEventCode)
        bypassData["bypassEvents"] = typedBypassList
        _write_cache_file(bypassPath, bypassData)

    try:
        cachePath.unlink(missing_ok=True)
    except OSError:
        return


def bypassed_events_for_season(season: int) -> list[str]:
    bypassPath = _bypass_file_path(season=season)
    bypassData = _read_cache_file(bypassPath)
    bypassList = bypassData.get("bypassEvents")
    if not isinstance(bypassList, list):
        return []
    typedBypassList = cast(list[str], bypassList)
    return typedBypassList


def _read_cache_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}

    try:
        data: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    if is_json_object(data):
        return data
    return {}


def _write_cache_file(path: Path, cacheData: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(cacheData, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _build_basic_auth_header() -> str:
    envPath = Path(__file__).resolve().parents[1] / ".env"
    load_dotenv(dotenv_path=envPath)

    username = os.getenv("AUTH_USERNAME")
    token = os.getenv("AUTH_TOKEN")
    if not username or not token:
        raise FRCAuthorizationError("Missing AUTH_USERNAME or AUTH_TOKEN in .env for FRC API authorization.")

    raw = f"{username}:{token}".encode("utf-8")
    encoded = base64.b64encode(raw).decode("ascii")
    return f"Basic {encoded}"


def fetch_frc_json(url: str, timeout: float = 15.0) -> dict[str, Any]:
    """
    Fetch JSON data from an FRC endpoint and return it as a dictionary.

    Args:
        url: Full endpoint URL.
        timeout: Request timeout in seconds.

    Returns:
        Parsed JSON object as dict.

    Raises:
        ValueError: If URL is empty.
        FRCAuthorizationError: If API auth credentials are missing.
        FRCNetworkError: If network request fails.
        FRCHTTPError: If HTTP status is not successful.
        FRCJSONDecodeError: If body cannot be decoded as JSON.
        FRCJSONTypeError: If decoded JSON is not a dict.
    """
    if not url or not url.strip():
        raise ValueError("url cannot be empty")

    headers = {
        "Accept": "application/json",
        "User-Agent": "goat-event-v2/26.4.0",
        "Authorization": _build_basic_auth_header(),
    }
    request = Request(url=url, headers=headers, method="GET")

    try:
        with urlopen(request, timeout=timeout) as response:
            bodyBytes = response.read()
    except HTTPError as exc:
        statusCode = getattr(exc, "code", "unknown")
        body = ""
        try:
            body = exc.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        raise FRCHTTPError(f"HTTP {statusCode} returned for URL '{url}'. Response: {body[:300]}") from exc
    except URLError as exc:
        raise FRCNetworkError(f"Request failed for URL '{url}': {exc}") from exc
    except TimeoutError as exc:
        raise FRCNetworkError(f"Request failed for URL '{url}': {exc}") from exc

    try:
        text = bodyBytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise FRCJSONDecodeError(f"Response from URL '{url}' is not UTF-8 text JSON.") from exc

    try:
        payload: Any = json.loads(text)
    except json.JSONDecodeError as exc:
        raise FRCJSONDecodeError(f"Response from URL '{url}' is not valid JSON. Body: {text[:300]}") from exc

    if not is_json_object(payload):
        raise FRCJSONTypeError(f"Expected JSON object (dict) from URL '{url}', got {type(payload).__name__}")

    return payload


def request_frc_json(url: str, key: str, season: int, eventCode: str, timeout: float = 15.0) -> dict[str, Any]:
    """
    Return cached FRC JSON by key when available; otherwise fetch and cache it.

    Cache layout:
        cache/{season}/{season}-{eventCode}.json
    """
    if not key or not key.strip():
        raise ValueError("key cannot be empty")
    normalizedEventCode = eventCode.strip()
    if not normalizedEventCode:
        raise ValueError("eventCode cannot be empty")

    cachePath = _cache_file_path(season=season, eventCode=normalizedEventCode)
    cacheData = _read_cache_file(cachePath)

    cachedValue = cacheData.get(key)
    if is_json_object(cachedValue):
        return cachedValue

    payload = fetch_frc_json(url=url, timeout=timeout)
    cacheData[key] = payload
    _write_cache_file(cachePath, cacheData)
    return payload


def _request_paginated_json(
    cachePath: Path,
    url: str,
    key: str,
    payloadKey: str,
    timeout: float = 15.0,
) -> dict[str, Any]:
    """
    Return cached paginated FRC JSON by key when available; otherwise fetch all pages and cache the merged payload.

    The cached payload keeps the original top-level object shape, but replaces `payloadKey`
    with the concatenated list from every page.
    """
    if not key or not key.strip():
        raise ValueError("key cannot be empty")
    if not payloadKey or not payloadKey.strip():
        raise ValueError("payloadKey cannot be empty")

    cacheData = _read_cache_file(cachePath)

    cachedValue = cacheData.get(key)
    if is_json_object(cachedValue):
        cachedDataValue = cachedValue.get(payloadKey)
        cachedTotal = cachedValue.get("teamCountTotal")
        cachedPageTotal = cachedValue.get("pageTotal")
        if isinstance(cachedDataValue, list):
            cachedData = cast(list[object], cachedDataValue)
            if isinstance(cachedTotal, int) and cachedTotal > 0 and len(cachedData) == cachedTotal:
                return cachedValue
            if not isinstance(cachedTotal, int) and cachedPageTotal == 1:
                return cachedValue

    mergedPayload: dict[str, Any] | None = None
    mergedData: list[object] = []
    pageCurrent = 1
    pageTotal = 1

    while pageCurrent <= pageTotal:
        separator = "&" if "?" in url else "?"
        pageUrl = f"{url}{separator}page={pageCurrent}"
        payload = fetch_frc_json(url=pageUrl, timeout=timeout)

        pageData = payload.get(payloadKey)
        if not isinstance(pageData, list):
            raise ValueError(f"Invalid event data format for '{payloadKey}': expected a list")
        typedPageData = cast(list[object], pageData)

        if mergedPayload is None:
            mergedPayload = dict(payload)

        mergedData.extend(typedPageData)

        rawPageTotal = payload.get("pageTotal")
        if isinstance(rawPageTotal, int) and rawPageTotal > 0:
            pageTotal = rawPageTotal

        pageCurrent += 1

    if mergedPayload is None:
        raise ValueError(f"Missing paginated payload for '{payloadKey}'")

    mergedPayload[payloadKey] = mergedData
    mergedPayload["pageCurrent"] = 1
    mergedPayload["pageTotal"] = 1

    teamCountTotal = mergedPayload.get("teamCountTotal")
    if isinstance(teamCountTotal, int):
        mergedPayload["teamCountTotal"] = len(mergedData)

    teamCountPage = mergedPayload.get("teamCountPage")
    if isinstance(teamCountPage, int):
        mergedPayload["teamCountPage"] = len(mergedData)

    cacheData[key] = mergedPayload
    _write_cache_file(cachePath, cacheData)
    return mergedPayload


def request_paginated_frc_json(
    url: str,
    key: str,
    payloadKey: str,
    season: int,
    eventCode: str,
    timeout: float = 15.0,
) -> dict[str, Any]:
    normalizedEventCode = eventCode.strip()
    if not normalizedEventCode:
        raise ValueError("eventCode cannot be empty")

    cachePath = _cache_file_path(season=season, eventCode=normalizedEventCode)
    return _request_paginated_json(cachePath, url, key, payloadKey, timeout)


def request_paginated_season_frc_json(
    url: str,
    key: str,
    payloadKey: str,
    season: int,
    timeout: float = 15.0,
) -> dict[str, Any]:
    """
    Return cached paginated season-level FRC JSON by key when available; otherwise fetch all pages and cache the merged payload.

    Cache layout:
        cache/{season}/SeasonData.json
    """
    cachePath = _season_cache_file_path(season=season)
    return _request_paginated_json(cachePath, url, key, payloadKey, timeout)


def request_season_frc_json(url: str, key: str, season: int, timeout: float = 15.0) -> dict[str, Any]:
    """
    Return cached FRC JSON by key when available; otherwise fetch and cache it.

    Cache layout:
        cache/{season}/SeasonData.json
    """
    if not key or not key.strip():
        raise ValueError("key cannot be empty")

    cachePath = _season_cache_file_path(season=season)
    cacheData = _read_cache_file(cachePath)

    cachedValue = cacheData.get(key)
    if is_json_object(cachedValue):
        return cachedValue

    payload = fetch_frc_json(url=url, timeout=timeout)
    cacheData[key] = payload
    _write_cache_file(cachePath, cacheData)
    return payload
