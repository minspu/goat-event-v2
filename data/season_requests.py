# Copyright (c) 2026 FRC Team 6907, The G.O.A.T
# Licensed under the MIT License.

from typing import cast
from data.frc_json import SeasonRequestType, request_paginated_season_frc_json, request_season_frc_json


FRC_API_BASE_URL = "https://frc-api.firstinspires.org/v3.0"


def _get_season_request_details(requestType: SeasonRequestType, season: int) -> tuple[str, str, str]:
    match requestType:
        case SeasonRequestType.EVENT_LISTING:
            return f"{season}/events", "events", "Events"
        case SeasonRequestType.TEAM_LISTING:
            return f"{season}/teams", "teams", "teams"


def request_season_data(requestType: SeasonRequestType, season: int) -> list[object]:
    route, cacheKey, payloadKey = _get_season_request_details(requestType, season)
    fullUrl = f"{FRC_API_BASE_URL}/{route}"
    if requestType is SeasonRequestType.TEAM_LISTING:
        payload = request_paginated_season_frc_json(fullUrl, cacheKey, payloadKey, season)
    else:
        payload = request_season_frc_json(fullUrl, cacheKey, season)

    data = payload.get(payloadKey)
    if data is None or not isinstance(data, list):
        raise ValueError(f"Invalid event data format for '{payloadKey}': expected a list")
    return cast(list[object], data)
