# Copyright (c) 2026 FRC Team 6907, The G.O.A.T
# Licensed under the MIT License.

from __future__ import annotations

from enum import IntEnum
from typing import Protocol
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from real.event import Event
    from real.match import Match, PlayoffRound
    from real.alliance import Alliance


class TournamentLevel(IntEnum):
    QUALIFICATION = 0
    PLAYOFF = 1


class TournamentType(IntEnum):
    NONE = 1
    REGIONAL = 2
    DISTRICT_EVENT = 3
    DISTRICT_CHAMPIONSHIP = 4
    DISTRICT_CHAMPIONSHIP_WITH_LEVELS = 5
    DISTRICT_CHAMPIONSHIP_DIVISION = 6
    CHAMPIONSHIP_SUBDIVISION = 7
    CHAMPIONSHIP_DIVISION = 8
    CHAMPIONSHIP = 9
    OFF_SEASON = 10
    OFF_SEASON_WITH_AZURE_SYNC = 11


class TournamentRule(Protocol):
    event: Event

    def __init__(self, event: Event): ...

    # Getters

    def get_playoff_from_round(self, round: PlayoffRound, part: int, match: int) -> Match: ...

    def get_round_part_winner(self, round: PlayoffRound, part: int) -> Alliance: ...

    def get_round_part_finalist(self, round: PlayoffRound, part: int) -> Alliance: ...
