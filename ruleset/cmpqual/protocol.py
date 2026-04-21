from __future__ import annotations

from typing import Protocol, Union
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from real.event import Event
    from real.team import Team


class CMPQualRule(Protocol):
    event: Event

    def __init__(self, event: Event): ...

    # CMP Eligibility Points Calculation

    def get_qualification_points(self, team: Team) -> int: ...

    def get_alliance_selection_points(self, team: Team) -> int: ...

    def get_playoff_round_points(self, team: Team) -> int: ...

    def get_team_age_points(self, team: Team) -> int: ...

    def get_award_points(self, team: Team) -> int: ...

    # CMP Direct Qualification

    def get_direct_qualification_info(self, team: Team) -> dict[str, Union[str, bool]]:
        """Returns a dict with `{"qualified": bool, "reason": str}`,
        where `qualified` indicates whether the team is directly qualified for CMP,
        and `reason` is the reason for the qualification or disqualification.
        """
        ...

    def get_direct_qualified_teams(self) -> list[Team]: ...
