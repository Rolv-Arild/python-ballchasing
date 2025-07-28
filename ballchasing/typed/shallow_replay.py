from dataclasses import dataclass, field
from typing import Optional, List

from ballchasing.typed.shared import _DictToTypeMixin, BasePlayer, BaseTeam, BaseReplay


@dataclass
class PlayerSR(BasePlayer):
    # start_time: float = 0.0
    # end_time: float = 0.0
    # name: str = ""
    # id: Optional[PlayerID] = None
    # pro: bool = False
    # mvp: bool = False
    # rank: Optional[Rank] = None
    score: int = 0


@dataclass
class TeamSR(BaseTeam):
    # name: str = ""
    goals: int = 0
    players: List[PlayerSR] = field(default_factory=list)

    def __eq__(self, other):
        if isinstance(other, TeamSR):
            for p1 in self.players:
                for p2 in other.players:
                    if p1 == p2:
                        break
                else:
                    return False
            return True
        return NotImplemented


@dataclass
class ShallowReplay(BaseReplay):
    # id: str = ""
    # link: str = ""
    # rocket_league_id: str = ""
    # recorder: str = ""
    # map_code: str = ""
    # map_name: str = ""
    # playlist_id: str = ""
    # playlist_name: str = ""
    # duration: int = 0
    # overtime: bool = False
    # overtime_seconds: int = 0
    # season: int = 0
    # season_type: str = ""
    # date: Optional[datetime] = None
    # visibility: str = ""
    # created: Optional[datetime] = None
    # uploader: Optional[User] = None
    # min_rank: Optional[Rank] = None
    # max_rank: Optional[Rank] = None
    # groups: List[BaseGroup] = field(default_factory=list)
    replay_title: str = ""  # title in deep replay
    date_has_tz: bool = False  # date_has_timezone in deep replay
    blue: Optional[TeamSR] = None
    orange: Optional[TeamSR] = None

    def scoreline(self):
        bg = self.blue.goals if self.blue else 0
        og = self.orange.goals if self.orange else 0
        return bg, og
