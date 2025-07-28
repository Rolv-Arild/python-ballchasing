from dataclasses import dataclass, fields, field
from datetime import datetime
from functools import total_ordering
from typing import get_args, Optional, List

from ballchasing.util import from_rfc3339


class _DictToTypeMixin:
    """
    Mixin class to convert dicts to their respective types in dataclasses.
    """

    def __post_init__(self):
        for field in fields(self):
            value = getattr(self, field.name)
            actual_type = field.type
            if args := get_args(field.type):
                actual_type = args[0]
            if isinstance(value, dict):
                new_value = actual_type(**value)
                setattr(self, field.name, new_value)
            elif isinstance(value, list):
                new_value = [actual_type(**item) if isinstance(item, dict) else item for item in value]
                setattr(self, field.name, new_value)
            elif isinstance(value, str) and actual_type is datetime:
                # Load rfc3339 formatted strings as datetime objects
                new_value = from_rfc3339(value)
                setattr(self, field.name, new_value)
            # else:  # For testing
            #     # Check that the value has the type specified in the dataclass field
            #     if value is not None and not isinstance(value, actual_type):
            #         if isinstance(value, int) and actual_type is float:
            #             pass  # ints can be converted losslessly to floats
            #         else:
            #             raise TypeError(f"Expected {field.name} to be of type {actual_type}, got {type(value)}")


@dataclass
class User:
    steam_id: str = ""
    name: str = ""
    profile_url: str = ""
    avatar: str = ""

    def __eq__(self, other):
        if isinstance(other, User):
            return self.steam_id == other.steam_id
        return False


@dataclass
class PlayerID:
    platform: str = ""
    id: str = ""
    player_number: int = 0

    def __repr__(self):
        if self.player_number == 0:
            return f"{self.platform}:{self.id}"
        return f"{self.platform}:{self.id}#{self.player_number}"


@total_ordering
@dataclass
class Rank:
    tier: int = 0
    division: int = 0
    name: str = ""
    id: str = ""

    def __eq__(self, other):
        return self.tier == other.tier and self.division == other.division

    def __lt__(self, other):
        return (self.tier, self.division) < (other.tier, other.division)

    @classmethod
    def from_id(cls, rank_id: str):
        """
        Create a Rank object from a rank ID string, e.g. "grand-champion-1"
        """
        from ballchasing.constants import Rank as RankConstants
        ranks = [r for r in RankConstants.ALL if r != "grand-champion"]
        if rank_id == RankConstants.GRAND_CHAMPION_LEGACY:
            rank_id = RankConstants.GRAND_CHAMPION_1
        try:
            tier = ranks.index(rank_id)
            division = 0  # Division 0 is not really a thing but ID doesn't include it
            name = rank_id.replace("-", " ").title().strip()
            name = name.replace("1", "I").replace("2", "II").replace("3", "III")
            name = name + " Division 0"
            return cls(tier=tier, division=division, name=name, id=rank_id)
        except ValueError:
            raise ValueError(f"Invalid rank ID: {rank_id}. Must be one of {ranks}.")

    @classmethod
    def from_name(cls, rank_name: str):
        rank_id = rank_name.lower().replace(" ", "-")
        rank_id = rank_id.replace("i", "1").replace("ii", "2").replace("iii", "3")
        if "-division-" in rank_id:
            rank_id, division = rank_id.split("-division-")
            division = int(division)
        else:
            division = 0

        res = cls.from_id(rank_id)
        res.division = division
        res.name = rank_name
        return res


@dataclass
class BasePlayer(_DictToTypeMixin):
    start_time: float = 0.0
    end_time: float = 0.0
    name: str = ""
    id: Optional[PlayerID] = None
    pro: bool = False
    mvp: bool = False
    rank: Optional[Rank] = None

    def __eq__(self, other):
        if isinstance(other, BasePlayer):
            return self.id == other.id
        return NotImplemented

    def is_bot(self):
        return self.id.id == "" and self.id.platform == ""


@dataclass
class BaseTeam(_DictToTypeMixin):
    name: str = ""
    # Further specified in subclasses, needed for methods:
    players: List[BasePlayer] = field(default_factory=list)

    def __eq__(self, other):
        # Teams are equal if all players are the same
        if isinstance(other, BaseTeam):
            for p1 in self.players:
                for p2 in other.players:
                    if p1 == p2:
                        break
                else:
                    return False
            return True
        return NotImplemented


@dataclass
class BasicGroup:  # Shared between replays and shallow/deep groups
    id: str = ""
    name: str = ""
    link: str = ""

    def __eq__(self, other):
        if isinstance(other, BasicGroup):
            return self.id == other.id
        return NotImplemented


@dataclass
class BaseGroup(BasicGroup, _DictToTypeMixin):  # Shared between shallow and deep groups
    created: Optional[datetime] = ""
    player_identification: str = ""
    team_identification: str = ""
    shared: bool = False


@dataclass
class BaseReplay(_DictToTypeMixin):  # Shared between shallow and deep replays
    id: str = ""
    link: str = ""
    rocket_league_id: str = ""
    recorder: str = ""
    map_code: str = ""
    map_name: str = ""
    playlist_id: str = ""
    playlist_name: str = ""
    duration: int = 0
    overtime: bool = False
    overtime_seconds: int = 0
    season: int = 0
    season_type: str = ""
    date: Optional[datetime] = None
    visibility: str = ""
    created: Optional[datetime] = None
    uploader: Optional[User] = None
    min_rank: Optional[Rank] = None
    max_rank: Optional[Rank] = None
    groups: List[BasicGroup] = field(default_factory=list)
    # Further specified in subclasses, needed for methods:
    blue: Optional[BaseTeam] = None
    orange: Optional[BaseTeam] = None

    def players(self):
        blue = self.blue.players if self.blue else []
        orange = self.orange.players if self.orange else []
        return blue + orange

    def teams(self):
        teams = []
        if self.blue:
            teams.append(self.blue)
        if self.orange:
            teams.append(self.orange)
        return teams

    def team_sizes(self):
        bs = len(self.blue.players) if self.blue else 0
        os = len(self.orange.players) if self.orange else 0
        return bs, os

    def __eq__(self, other):
        if isinstance(other, BaseReplay):
            return self.id == other.id or self.rocket_league_id == other.rocket_league_id
        return NotImplemented
