"""
Hand-written methods of the typed response objects.

The classes in models.py are generated from the OpenAPI document and inherit these mixins (see METHODS in
scripts/generate_models.py). Mixins only hold methods, no fields. A mixin defining __eq__ or __repr__ makes the
generator turn off the dataclass's own, so the mixin's is used.
"""
from functools import total_ordering


class UserMethods:
    def __eq__(self, other):
        if isinstance(other, UserMethods):
            return self.steam_id == other.steam_id
        return False


class PlayerIdMethods:
    def __repr__(self):
        if self.player_number == 0:
            return f"{self.platform}:{self.id}"
        return f"{self.platform}:{self.id}#{self.player_number}"


@total_ordering
class RankMethods:
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


class BasePlayerMethods:
    def __eq__(self, other):
        if isinstance(other, BasePlayerMethods):
            return self.id == other.id
        return NotImplemented

    def is_bot(self):
        return self.id is None or (self.id.id == "" and self.id.platform == "")


class BaseTeamMethods:
    def __eq__(self, other):
        # Teams are equal if all players are the same
        if isinstance(other, BaseTeamMethods):
            for p1 in self.players:
                for p2 in other.players:
                    if p1 == p2:
                        break
                else:
                    return False
            return True
        return NotImplemented


class BasicGroupMethods:
    def __eq__(self, other):
        if isinstance(other, BasicGroupMethods):
            return self.id == other.id
        return NotImplemented


class BaseReplayMethods:
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
        if isinstance(other, BaseReplayMethods):
            return self.id == other.id or self.rocket_league_id == other.rocket_league_id
        return NotImplemented


class DeepReplayMethods:
    def scoreline(self):
        try:
            bg = self.blue.stats.core.goals
        except AttributeError:
            bg = 0
        try:
            og = self.orange.stats.core.goals
        except AttributeError:
            og = 0
        return bg, og


class ShallowReplayMethods:
    def scoreline(self):
        bg = self.blue.goals if self.blue else 0
        og = self.orange.goals if self.orange else 0
        return bg, og
