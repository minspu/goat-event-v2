# Copyright (c) 2026 FRC Team 6907, The G.O.A.T
# Licensed under the MIT License.

from __future__ import annotations

from datetime import datetime
from enum import IntEnum
from typing import Optional, Union, Any, cast
from typing import TYPE_CHECKING

from real.alliance import (
    AllianceBase,
    AnonymousAlliance,
    Alliance,
    AllianceColor,
    AllianceRole,
)
from ruleset.tournament.protocol import TournamentLevel

if TYPE_CHECKING:
    from real.event import Event
    from real.team import Team


class MatchResult(IntEnum):
    DQ = 0
    LOSS = 1
    WIN = 2
    TIE = 3


class PlayoffRound(IntEnum):
    QUARTER = 0
    SEMI = 1
    FINAL = 2


class Match:
    def __init__(
        self, event: Event, tournamentLevel: TournamentLevel, matchNumber: int
    ):
        self.event: Event = event
        self.tournamentLevel: TournamentLevel = tournamentLevel
        self.isReplay: bool = False
        self.matchVideoLink: Optional[str] = None
        self.matchNumber: int = matchNumber
        self.dqTeams: list[Team] = []
        self.redScore: list[Union[int, float]] = []  # waiting for the event to assign
        self.blueScore: list[Union[int, float]] = []
        self.redScoreDetails: dict[str, Any] = {}
        self.blueScoreDetails: dict[str, Any] = {}
        self.generalScoreDetails: dict[str, Any] = {}
        self.winningAlliance: Optional[AllianceColor] = None
        self.redAlliance: Optional[AllianceBase] = None
        self.blueAlliance: Optional[AllianceBase] = None
        self.station: dict[AllianceColor, dict[AllianceRole, Optional[Team]]] = {
            AllianceColor.RED: {},
            AllianceColor.BLUE: {},
        }
        if tournamentLevel == TournamentLevel.QUALIFICATION:
            # this is assigned after scheduled
            self.redAlliance = AnonymousAlliance(event)
            self.blueAlliance = AnonymousAlliance(event)

        self.actualStartTime: Optional[datetime] = None
        self.postResultTime: Optional[datetime] = None

    def __str__(self):
        if self.tournamentLevel == TournamentLevel.QUALIFICATION:
            return f"<Qualification {self.matchNumber}>"
        elif self.tournamentLevel == TournamentLevel.PLAYOFF:
            if self.event.season <= 2022:
                if self.matchNumber <= 12:
                    if self.matchNumber % 3 == 0:
                        return f"<Quarter {(self.matchNumber - 1) // 3 + 1} Tiebreaker>"
                    else:
                        return f"<Quarter {(self.matchNumber - 1) // 3 + 1} Match {self.matchNumber % 3}>"
                elif self.matchNumber <= 18:
                    if self.matchNumber % 3 == 0:
                        return f"<Semi {(self.matchNumber - 1) // 3 - 3} Tiebreaker>"
                    else:
                        return f"<Semi {(self.matchNumber - 1) // 3 - 3} Match {self.matchNumber % 3}>"
                elif self.matchNumber <= 20:
                    return f"<Final {self.matchNumber - 18}>"
                else:
                    return f"<Final Tiebreaker>"
            else:
                if self.matchNumber <= 13:
                    return f"<Playoff Match {self.matchNumber}>"
                elif self.matchNumber <= 15:
                    return f"<Final {self.matchNumber - 13}>"
                else:
                    return f"<Final Tiebreaker>"
        raise ValueError(
            f"Invalid tournament level {self.tournamentLevel} for match {self.matchNumber}"
        )

    def __repr__(self):
        return self.__str__()

    # Registration

    def assign_team(
        self,
        team: Team,
        station: AllianceRole,
        allianceColor: AllianceColor,
        disqualified: bool,
    ):
        currentMatch = cast(Match, self)
        self.station[allianceColor][station] = team
        if (
            self.tournamentLevel == TournamentLevel.QUALIFICATION
        ):  # only quals should assign teams to alliance
            team.qualsMatches.append(currentMatch)
            redAlliance, blueAlliance = (
                cast(AnonymousAlliance, self.redAlliance),
                cast(AnonymousAlliance, self.blueAlliance),
            )
            if allianceColor == AllianceColor.RED:
                redAlliance.assign_team(
                    team, station
                )  # pyright: ignore[reportOptionalMemberAccess]
            else:
                blueAlliance.assign_team(
                    team, station
                )  # pyright: ignore[reportOptionalMemberAccess]
        elif self.tournamentLevel == TournamentLevel.PLAYOFF:
            team.playoffMatches.append(currentMatch)
        if disqualified:
            self.dqTeams.append(team)

    def assign_alliance(self, alliance: Alliance, allianceColor: AllianceColor):
        currentMatch = cast(Match, self)
        if (
            self.tournamentLevel == TournamentLevel.PLAYOFF
        ):  # only playoffs should assign alliances to match
            if allianceColor == AllianceColor.RED:
                self.redAlliance = alliance
            else:
                self.blueAlliance = alliance
            alliance.playoffMatches.append(currentMatch)

    # Getters

    def get_alliance(self, allianceColor: AllianceColor) -> AllianceBase:
        if allianceColor == AllianceColor.RED:
            alliance = self.redAlliance
        else:
            alliance = self.blueAlliance
        if alliance is not None:
            return alliance
        raise ValueError(
            f"Alliance is not assigned for match {self} with alliance color {allianceColor}"
        )

    def get_team_from_station(
        self, allianceColor: AllianceColor, station: AllianceRole
    ) -> Team:
        team = self.station.get(allianceColor, {}).get(station)
        if team is None:
            raise ValueError(
                f"Team is not assigned for match {self} at station {station}"
            )
        return team

    def get_result(self) -> dict[MatchResult, list[AllianceBase]]:
        wins: list[AllianceBase] = []
        loss: list[AllianceBase] = []
        ties: list[AllianceBase] = []
        dq: list[AllianceBase] = []
        if self.redAlliance and self.blueAlliance:
            winningAlliance = self.winningAlliance
            if winningAlliance is not None:
                if winningAlliance == AllianceColor.RED:
                    wins.append(self.redAlliance)
                    loss.append(self.blueAlliance)
                elif winningAlliance == AllianceColor.BLUE:
                    wins.append(self.blueAlliance)
                    loss.append(self.redAlliance)
                else:
                    ties.append(self.redAlliance)
                    ties.append(self.blueAlliance)
                if self.tournamentLevel == TournamentLevel.PLAYOFF:
                    if any(
                        team in self.dqTeams for team in self.redAlliance.teams.values()
                    ):
                        dq.append(self.redAlliance)
                    if any(
                        team in self.dqTeams
                        for team in self.blueAlliance.teams.values()
                    ):
                        dq.append(self.blueAlliance)
                return {
                    MatchResult.DQ: dq,
                    MatchResult.WIN: wins,
                    MatchResult.LOSS: loss,
                    MatchResult.TIE: ties,
                }
            raise ValueError(f"Winning Alliance is not assigned for match {self}")
        raise ValueError(f"Alliance is not assigned for match {self}")

    def get_result_by_alliance(self, alliance: AllianceBase) -> MatchResult:
        if alliance not in (self.redAlliance, self.blueAlliance):
            raise ValueError(
                f"Alliance {alliance} is not in match {self} or not assigned yet"
            )
        if any(team in self.dqTeams for team in alliance.teams.values()):
            return MatchResult.DQ
        winningAlliance = self.winningAlliance

        if winningAlliance is not None:
            if winningAlliance == AllianceColor.RED:
                return (
                    MatchResult.WIN
                    if alliance == self.redAlliance
                    else MatchResult.LOSS
                )
            elif winningAlliance == AllianceColor.BLUE:
                return (
                    MatchResult.WIN
                    if alliance == self.blueAlliance
                    else MatchResult.LOSS
                )
            else:
                return MatchResult.TIE
        raise ValueError(f"Winner is not assigned for match {self}")

    def get_result_by_team(self, team: Team) -> MatchResult:
        if self.redAlliance and self.blueAlliance:
            if (
                team not in self.redAlliance.teams.values()
                and team not in self.blueAlliance.teams.values()
            ):
                raise ValueError(f"Team {team} is not in match {self}")
            if team in self.dqTeams:
                return MatchResult.DQ
            winningAlliance = self.winningAlliance
            if winningAlliance is None and self.redScore and self.blueScore:
                if self.redScore > self.blueScore:
                    winningAlliance = AllianceColor.RED
                elif self.redScore < self.blueScore:
                    winningAlliance = AllianceColor.BLUE
                else:
                    winningAlliance = AllianceColor.NONE

            if winningAlliance is not None:
                if winningAlliance == AllianceColor.RED:
                    return (
                        MatchResult.WIN
                        if team in self.redAlliance.teams.values()
                        else MatchResult.LOSS
                    )
                elif winningAlliance == AllianceColor.BLUE:
                    return (
                        MatchResult.WIN
                        if team in self.blueAlliance.teams.values()
                        else MatchResult.LOSS
                    )
                else:
                    return MatchResult.TIE
        raise ValueError(f"Alliance or score is not assigned for match {self}")

    def get_alliance_by_team(self, team: Team) -> AllianceBase:
        if self.redAlliance and self.blueAlliance:
            if team in self.redAlliance.teams.values():
                return self.redAlliance
            elif team in self.blueAlliance.teams.values():
                return self.blueAlliance
            else:
                raise ValueError(f"Team {team} is not in match {self}")
        raise ValueError(f"Alliances are not assigned for match {self}")
