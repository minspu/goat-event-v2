# Copyright (c) 2026 FRC Team 6907, The G.O.A.T
# Licensed under the MIT License.

from __future__ import annotations

from typing import Optional, Union
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from real.event import Event
    from real.alliance import Alliance, AllianceRole
    from real.match import Match, MatchResult


class Team:
    """
    A `Team` represents a team in a specific event,
    that is, `Team` instances are different if the event changes.
    """

    def __init__(self, teamNumber: int, event: Event):
        self.teamNumber: int = teamNumber
        self.event: Event = event

        # waiting for requests
        self.rookieYear: int = 0
        self.nameShort: Optional[str] = None
        self.nameFull: Optional[str] = None
        self.districtCode: Optional[str] = None

        # waiting for the event to assign
        self.sortOrder: Optional[tuple[Union[int, float], ...]] = None
        self.alliance: Optional[Alliance] = None
        self.allianceRole: Optional[AllianceRole] = None
        self.ranking: int = 0
        self.awards: list[str] = []

        # waiting to match
        self.qualsMatches: list[Match] = []
        self.playoffMatches: list[Match] = []

        self.seasonTeam: Optional[SeasonTeam] = None

    def __str__(self):
        return f"<Team {self.teamNumber}>"

    def __repr__(self):
        return self.__str__()

    @property
    def matches(self) -> list[Match]:
        return self.qualsMatches + self.playoffMatches

    def register_alliance(self, alliance: Alliance, allianceRole: AllianceRole):
        self.alliance = alliance
        self.allianceRole = allianceRole

    # Getters

    def get_succession(self) -> Optional[int]:
        """
        Get the alliance-selection succession of the team,
        which is the order of selection the team is selected
        in the alliance selection.
        For example, if the team is the Alliance 4 captain,
        then the succession is 7, because it is the 7th team
        to join in an alliance in the alliance selection.
        """
        if self.alliance is not None:
            match self.allianceRole:
                case 1:
                    return self.alliance.allianceNumber * 2 - 1
                case 2:
                    return self.alliance.allianceNumber * 2
                case 3:
                    return 25 - self.alliance.allianceNumber
                case 4:
                    return 24 + self.alliance.allianceNumber
                case _:
                    return None
        else:
            return None

    def get_succession_of_selection(self) -> Optional[int]:
        """
        Get the succession of selection of the team, which is
        the current rank of the team among the unselected teams
        when the team is selected.
        For example, if the team is rank 3 and is picked by
        Alliance 1, then the succession of selection is 2, because
        this team is the second best-ranked team among the
        unselected teams (2 and 3) when rank 1 is picking.
        """
        if self.alliance is not None:
            match self.allianceRole:
                case 1:
                    return 0
                case 2:
                    darkhorses = 0
                    for allianceNumber in range(1, self.alliance.allianceNumber):
                        if (
                            self.event.get_alliance_from_number(allianceNumber)
                            .teams[1]
                            .ranking
                            > self.ranking
                        ):
                            darkhorses += 1
                    return (
                        self.ranking
                        - (self.alliance.allianceNumber * 2 - 1)
                        + darkhorses
                    )
                case 3:
                    darkhorses = 0
                    for allianceNumber in range(8, self.alliance.allianceNumber, -1):
                        if (
                            self.event.get_alliance_from_number(allianceNumber)
                            .teams[2]
                            .ranking
                            > self.ranking
                        ):
                            darkhorses += 1
                    for allianceNumber in range(1, 9):
                        if (
                            self.event.get_alliance_from_number(allianceNumber)
                            .teams[1]
                            .ranking
                            > self.ranking
                        ):
                            darkhorses += 1
                    return (
                        self.ranking - (24 - self.alliance.allianceNumber) + darkhorses
                    )
                case 4:
                    darkhorses = 0
                    for allianceNumber in range(1, self.alliance.allianceNumber):
                        if (
                            self.event.get_alliance_from_number(allianceNumber)
                            .teams[3]
                            .ranking
                            > self.ranking
                        ):
                            darkhorses += 1
                    for allianceNumber in range(8, 0, -1):
                        if (
                            self.event.get_alliance_from_number(allianceNumber)
                            .teams[2]
                            .ranking
                            > self.ranking
                        ):
                            darkhorses += 1
                    for allianceNumber in range(1, 9):
                        if (
                            self.event.get_alliance_from_number(allianceNumber)
                            .teams[1]
                            .ranking
                            > self.ranking
                        ):
                            darkhorses += 1
                    return (
                        self.ranking - (23 + self.alliance.allianceNumber) + darkhorses
                    )
                case _:
                    return None
        else:
            return None

    def get_matches_by_result(self, targetResult: list[MatchResult]) -> list[Match]:
        result: list[Match] = []
        for match in self.matches:
            if match.get_result_by_team(self) in targetResult:
                result.append(match)
        return result


class SeasonTeam:
    """
    A `SeasonTeam` represents a team in the whole season.
    It is automatically created when a Season is initialized.
    """

    def __init__(self, season: int, teamNumber: int):
        self.teamNumber: int = teamNumber
        self.season: int = season
        self.events: list[tuple[int, Event]] = []
        self.eventTeams: list[tuple[int, Team]] = []

    def __str__(self):
        return f"<SeasonTeam {self.teamNumber}>"

    def __repr__(self):
        return self.__str__()

    # Getters

    def get_events_by_weeks(self, weeks: list[int]) -> list[Team]:
        """
        The `Team`s a `SeasonTeam` shows up as before and during a week.
        """
        events: list[Team] = []
        for team in self.eventTeams:
            if team[0] in weeks:
                events.append(team[1])
        return events
