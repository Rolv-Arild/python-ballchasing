from dataclasses import field
from typing import List, Optional

from ballchasing.typed.shared import _DictToTypeMixin, User, BaseGroup, _BaseModel, model


@model
class CreatorDG(User):
    # steam_id: str = ""
    # name: str = ""
    # profile_url: str = ""
    # avatar: str = ""
    avatar_full: str = ""
    avatar_medium: str = ""


@model
class PlayerCumulativeCoreStatsDG(_BaseModel):
    shots: int = 0
    shots_against: int = 0
    goals: int = 0
    goals_against: int = 0
    saves: int = 0
    assists: int = 0
    score: int = 0
    mvp: int = 0
    shooting_percentage: float = 0.0
    epic_saves: int = 0
    clears: int = 0
    centers: int = 0
    aerial_hits: int = 0
    first_touches: int = 0
    flip_resets: int = 0
    crossbar_hits: int = 0
    bicycle_hits: int = 0
    juggle_hits: int = 0


@model
class PlayerCumulativeBoostStatsDG(_BaseModel):
    bpm: float = 0.0
    bcpm: float = 0.0
    avg_amount: float = 0.0
    amount_collected: int = 0
    amount_stolen: int = 0
    amount_collected_big: int = 0
    amount_stolen_big: int = 0
    amount_collected_small: int = 0
    amount_stolen_small: int = 0
    count_collected_big: int = 0
    count_stolen_big: int = 0
    count_collected_small: int = 0
    count_stolen_small: int = 0
    time_zero_boost: float = 0.0
    percent_zero_boost: float = 0.0
    time_full_boost: float = 0.0
    percent_full_boost: float = 0.0
    amount_overfill: int = 0
    amount_overfill_stolen: int = 0
    amount_used_while_supersonic: int = 0
    time_boost_0_25: float = 0.0
    time_boost_25_50: float = 0.0
    time_boost_50_75: float = 0.0
    time_boost_75_100: float = 0.0
    percent_boost_0_25: float = 0.0
    percent_boost_25_50: float = 0.0
    percent_boost_50_75: float = 0.0
    percent_boost_75_100: float = 0.0


@model
class PlayerCumulativeMovementStatsDG(_BaseModel):
    avg_speed: float = 0.0
    total_distance: int = 0
    time_supersonic_speed: float = 0.0
    time_boost_speed: float = 0.0
    time_slow_speed: float = 0.0
    time_ground: float = 0.0
    time_low_air: float = 0.0
    time_high_air: float = 0.0
    time_powerslide: float = 0.0
    count_powerslide: int = 0
    avg_powerslide_duration: float = 0.0
    avg_speed_percentage: float = 0.0
    percent_slow_speed: float = 0.0
    percent_boost_speed: float = 0.0
    percent_supersonic_speed: float = 0.0
    percent_ground: float = 0.0
    percent_low_air: float = 0.0
    percent_high_air: float = 0.0
    time_wall: float = 0.0
    percent_wall: float = 0.0


@model
class PlayerCumulativePositioningStatsDG(_BaseModel):
    avg_distance_to_ball: float = 0.0
    avg_distance_to_ball_possession: float = 0.0
    avg_distance_to_ball_no_possession: float = 0.0
    time_defensive_third: float = 0.0
    time_neutral_third: float = 0.0
    time_offensive_third: float = 0.0
    time_defensive_half: float = 0.0
    time_offensive_half: float = 0.0
    time_behind_ball: float = 0.0
    time_infront_ball: float = 0.0
    time_most_back: float = 0.0
    time_most_forward: float = 0.0
    goals_against_while_last_defender: int = 0
    time_closest_to_ball: float = 0.0
    time_farthest_from_ball: float = 0.0
    percent_defensive_third: float = 0.0
    percent_offensive_third: float = 0.0
    percent_neutral_third: float = 0.0
    percent_defensive_half: float = 0.0
    percent_offensive_half: float = 0.0
    percent_behind_ball: float = 0.0
    percent_infront_ball: float = 0.0
    avg_distance_to_mates: float = 0.0
    percent_most_back: float = 0.0
    percent_most_forward: float = 0.0
    percent_closest_to_ball: float = 0.0
    percent_farthest_from_ball: float = 0.0


@model
class PlayerCumulativeDemoStatsDG(_BaseModel):
    inflicted: int = 0
    taken: int = 0
    inflicted_in_defensive_half: int = 0
    inflicted_in_offensive_half: int = 0
    taken_in_defensive_half: int = 0
    taken_in_offensive_half: int = 0


@model
class PlayerCumulativeStatsDG(_BaseModel, _DictToTypeMixin):
    games: int = 0
    wins: int = 0
    win_percentage: float = 0
    play_duration: int = 0
    core: Optional[PlayerCumulativeCoreStatsDG] = None
    boost: Optional[PlayerCumulativeBoostStatsDG] = None
    movement: Optional[PlayerCumulativeMovementStatsDG] = None
    positioning: Optional[PlayerCumulativePositioningStatsDG] = None
    demo: Optional[PlayerCumulativeDemoStatsDG] = None


@model
class PlayerAverageCoreStatsDG(_BaseModel):
    shots: float = 0.0
    shots_against: int = 0
    goals: float = 0.0
    goals_against: float = 0.0
    saves: float = 0.0
    assists: float = 0.0
    score: float = 0.0
    mvp: int = 0
    shooting_percentage: float = 0.0
    epic_saves: float = 0.0
    clears: float = 0.0
    centers: float = 0.0
    aerial_hits: float = 0.0
    first_touches: float = 0.0
    flip_resets: float = 0.0
    crossbar_hits: float = 0.0
    bicycle_hits: float = 0.0
    juggle_hits: float = 0.0


@model
class PlayerAverageBoostStatsDG(_BaseModel):
    bpm: float = 0.0
    bcpm: float = 0.0
    avg_amount: float = 0.0
    amount_collected: float = 0.0
    amount_stolen: float = 0.0
    amount_collected_big: int = 0
    amount_stolen_big: float = 0.0
    amount_collected_small: float = 0.0
    amount_stolen_small: int = 0
    count_collected_big: float = 0.0
    count_stolen_big: float = 0.0
    count_collected_small: float = 0.0
    count_stolen_small: float = 0.0
    time_zero_boost: float = 0.0
    percent_zero_boost: float = 0.0
    time_full_boost: float = 0.0
    percent_full_boost: float = 0.0
    amount_overfill: int = 0
    amount_overfill_stolen: int = 0
    amount_used_while_supersonic: float = 0.0
    time_boost_0_25: float = 0.0
    time_boost_25_50: float = 0.0
    time_boost_50_75: float = 0.0
    time_boost_75_100: float = 0.0
    percent_boost_0_25: float = 0.0
    percent_boost_25_50: float = 0.0
    percent_boost_50_75: float = 0.0
    percent_boost_75_100: float = 0.0


@model
class PlayerAverageMovementStatsDG(_BaseModel):
    avg_speed: float = 0.0
    total_distance: int = 0
    time_supersonic_speed: float = 0.0
    time_boost_speed: float = 0.0
    time_slow_speed: float = 0.0
    time_ground: float = 0.0
    time_low_air: float = 0.0
    time_high_air: float = 0.0
    time_powerslide: float = 0.0
    count_powerslide: float = 0.0
    avg_powerslide_duration: float = 0.0
    avg_speed_percentage: float = 0.0
    percent_slow_speed: float = 0.0
    percent_boost_speed: float = 0.0
    percent_supersonic_speed: float = 0.0
    percent_ground: float = 0.0
    percent_low_air: float = 0.0
    percent_high_air: float = 0.0
    time_wall: float = 0.0
    percent_wall: float = 0.0


@model
class PlayerAveragePositioningStatsDG(_BaseModel):
    avg_distance_to_ball: float = 0.0
    avg_distance_to_ball_possession: float = 0.0
    avg_distance_to_ball_no_possession: float = 0.0
    time_defensive_third: float = 0.0
    time_neutral_third: float = 0.0
    time_offensive_third: float = 0.0
    time_defensive_half: float = 0.0
    time_offensive_half: float = 0.0
    time_behind_ball: float = 0.0
    time_infront_ball: float = 0.0
    time_most_back: float = 0.0
    time_most_forward: float = 0.0
    goals_against_while_last_defender: float = 0.0
    time_closest_to_ball: float = 0.0
    time_farthest_from_ball: float = 0.0
    percent_defensive_third: float = 0.0
    percent_offensive_third: float = 0.0
    percent_neutral_third: float = 0.0
    percent_defensive_half: float = 0.0
    percent_offensive_half: float = 0.0
    percent_behind_ball: float = 0.0
    percent_infront_ball: float = 0.0
    avg_distance_to_mates: float = 0.0
    percent_most_back: float = 0.0
    percent_most_forward: float = 0.0
    percent_closest_to_ball: float = 0.0
    percent_farthest_from_ball: float = 0.0


@model
class PlayerAverageDemoStatsDG(_BaseModel):
    inflicted: float = 0.0
    taken: float = 0.0
    inflicted_in_defensive_half: float = 0.0
    inflicted_in_offensive_half: float = 0.0
    taken_in_defensive_half: float = 0.0
    taken_in_offensive_half: float = 0.0


@model
class PlayerAverageStatsDG(_BaseModel, _DictToTypeMixin):
    core: Optional[PlayerAverageCoreStatsDG] = None
    boost: Optional[PlayerAverageBoostStatsDG] = None
    movement: Optional[PlayerAverageMovementStatsDG] = None
    positioning: Optional[PlayerAveragePositioningStatsDG] = None
    demo: Optional[PlayerAverageDemoStatsDG] = None


@model
class TeamCumulativeCoreStatsDG(_BaseModel):
    shots: int = 0
    shots_against: int = 0
    goals: int = 0
    goals_against: int = 0
    saves: int = 0
    assists: int = 0
    score: int = 0
    shooting_percentage: float = 0.0
    epic_saves: int = 0
    clears: int = 0
    centers: int = 0
    aerial_hits: int = 0
    first_touches: int = 0
    flip_resets: int = 0
    crossbar_hits: int = 0
    bicycle_hits: int = 0
    juggle_hits: int = 0


@model
class TeamCumulativeBoostStatsDG(_BaseModel):
    amount_collected: int = 0
    amount_stolen: int = 0
    amount_collected_big: int = 0
    amount_stolen_big: int = 0
    amount_collected_small: int = 0
    amount_stolen_small: int = 0
    count_collected_big: int = 0
    count_stolen_big: int = 0
    count_collected_small: int = 0
    count_stolen_small: int = 0
    time_zero_boost: float = 0.0
    percent_zero_boost: float = 0.0
    time_full_boost: float = 0.0
    percent_full_boost: float = 0.0
    amount_overfill: int = 0
    amount_overfill_stolen: int = 0
    amount_used_while_supersonic: int = 0
    time_boost_0_25: float = 0.0
    time_boost_25_50: float = 0.0
    time_boost_50_75: float = 0.0
    time_boost_75_100: float = 0.0
    bpm: float = 0.0
    bcpm: float = 0.0
    avg_amount: float = 0.0


@model
class TeamCumulativeMovementStatsDG(_BaseModel):
    total_distance: int = 0
    time_supersonic_speed: float = 0.0
    time_boost_speed: float = 0.0
    time_slow_speed: float = 0.0
    time_ground: float = 0.0
    time_low_air: int = 0
    time_high_air: float = 0.0
    time_powerslide: float = 0.0
    count_powerslide: int = 0
    time_wall: float = 0.0


@model
class TeamCumulativePositioningStatsDG(_BaseModel):
    time_defensive_third: float = 0.0
    time_neutral_third: float = 0.0
    time_offensive_third: float = 0.0
    time_defensive_half: float = 0.0
    time_offensive_half: float = 0.0
    time_behind_ball: float = 0.0
    time_infront_ball: float = 0.0
    avg_distance_to_ball: int = 0
    avg_distance_to_ball_possession: int = 0
    avg_distance_to_ball_no_possession: int = 0


@model
class TeamCumulativeDemoStatsDG(_BaseModel):
    inflicted: int = 0
    taken: int = 0
    inflicted_in_defensive_half: int = 0
    inflicted_in_offensive_half: int = 0
    taken_in_defensive_half: int = 0
    taken_in_offensive_half: int = 0


@model
class TeamCumulativeStatsDG(_BaseModel, _DictToTypeMixin):
    games: int = 0
    wins: int = 0
    win_percentage: float = 0
    play_duration: int = 0
    core: Optional[TeamCumulativeCoreStatsDG] = None
    boost: Optional[TeamCumulativeBoostStatsDG] = None
    movement: Optional[TeamCumulativeMovementStatsDG] = None
    positioning: Optional[TeamCumulativePositioningStatsDG] = None
    demo: Optional[TeamCumulativeDemoStatsDG] = None


@model
class TeamAverageCoreStatsDG(_BaseModel):
    shots: float = 0.0
    shots_against: int = 0
    goals: int = 0
    goals_against: float = 0.0
    saves: float = 0.0
    assists: float = 0.0
    score: float = 0.0
    shooting_percentage: float = 0.0
    epic_saves: float = 0.0
    clears: float = 0.0
    centers: float = 0.0
    aerial_hits: float = 0.0
    first_touches: float = 0.0
    flip_resets: float = 0.0
    crossbar_hits: float = 0.0
    bicycle_hits: float = 0.0
    juggle_hits: float = 0.0


@model
class TeamAverageBoostStatsDG(_BaseModel):
    bpm: int = 0
    bcpm: float = 0.0
    avg_amount: float = 0.0
    amount_collected: float = 0.0
    amount_stolen: float = 0.0
    amount_collected_big: float = 0.0
    amount_stolen_big: float = 0.0
    amount_collected_small: float = 0.0
    amount_stolen_small: float = 0.0
    count_collected_big: float = 0.0
    count_stolen_big: float = 0.0
    count_collected_small: float = 0.0
    count_stolen_small: float = 0.0
    time_zero_boost: float = 0.0
    percent_zero_boost: float = 0.0
    time_full_boost: float = 0.0
    percent_full_boost: float = 0.0
    amount_overfill: int = 0
    amount_overfill_stolen: int = 0
    amount_used_while_supersonic: int = 0
    time_boost_0_25: float = 0.0
    time_boost_25_50: float = 0.0
    time_boost_50_75: float = 0.0
    time_boost_75_100: float = 0.0


@model
class TeamAverageMovementStatsDG(_BaseModel):
    total_distance: float = 0.0
    time_supersonic_speed: float = 0.0
    time_boost_speed: float = 0.0
    time_slow_speed: float = 0.0
    time_ground: float = 0.0
    time_low_air: float = 0.0
    time_high_air: float = 0.0
    time_powerslide: float = 0.0
    count_powerslide: float = 0.0
    time_wall: float = 0.0


@model
class TeamAveragePositioningStatsDG(_BaseModel):
    time_defensive_third: float = 0.0
    time_neutral_third: float = 0.0
    time_offensive_third: float = 0.0
    time_defensive_half: float = 0.0
    time_offensive_half: float = 0.0
    time_behind_ball: float = 0.0
    time_infront_ball: float = 0.0
    avg_distance_to_ball: float = 0.0
    avg_distance_to_ball_possession: float = 0.0
    avg_distance_to_ball_no_possession: int = 0


@model
class TeamAverageDemoStatsDG(_BaseModel):
    inflicted: float = 0.0
    taken: float = 0.0
    inflicted_in_defensive_half: float = 0.0
    inflicted_in_offensive_half: float = 0.0
    taken_in_defensive_half: float = 0.0
    taken_in_offensive_half: float = 0.0


@model
class TeamAverageStatsDG(_BaseModel, _DictToTypeMixin):
    core: Optional[TeamAverageCoreStatsDG] = None
    boost: Optional[TeamAverageBoostStatsDG] = None
    movement: Optional[TeamAverageMovementStatsDG] = None
    positioning: Optional[TeamAveragePositioningStatsDG] = None
    demo: Optional[TeamAverageDemoStatsDG] = None


@model
class PlayerDG(_BaseModel):
    platform: str = ""
    id: str = ""
    name: str = ""
    team: str = ""


@model
class PlayerWithStatsDG(PlayerDG, _DictToTypeMixin):
    # platform: str = ""
    # id: str = ""
    # name: str = ""
    # team: str = ""
    cumulative: Optional[PlayerCumulativeStatsDG] = None
    game_average: Optional[PlayerAverageStatsDG] = None


@model
class TeamDG(_BaseModel, _DictToTypeMixin):
    name: str = ""
    players: List[PlayerDG] = field(default_factory=list)
    cumulative: Optional[TeamCumulativeStatsDG] = None
    game_average: Optional[TeamAverageStatsDG] = None
    id: str = ""


@model
class GroupDuplicates(_BaseModel):
    total_replays: int = 0
    duplicate_replays: int = 0  # total_replays - unique_games
    unique_games: int = 0


@model
class DeepGroup(BaseGroup):
    # id: str = ""
    # link: str = ""
    # name: str = ""
    # created: Optional[datetime] = None
    # player_identification: str = ""
    # team_identification: str = ""
    # shared: bool = False
    status: str = ""
    creator: Optional[CreatorDG] = None
    players: List[PlayerWithStatsDG] = field(default_factory=list)
    teams: List[TeamDG] = field(default_factory=list)
    dedup: bool = False
    failed_replays: List[str] = field(default_factory=list)
    duplicates: Optional[GroupDuplicates] = None
