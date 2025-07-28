from dataclasses import dataclass, field
from typing import Optional, List

from ballchasing.typed.shared import _DictToTypeMixin, BasePlayer, BaseReplay, BaseTeam


@dataclass
class CameraSettings:
    fov: int = 0
    height: int = 0
    pitch: int = 0
    distance: int = 0
    stiffness: float = 0.0
    swivel_speed: float = 0.0
    transition_speed: int = 0


@dataclass
class TeamBallStatsDR:
    possession_time: float = 0.0
    time_in_side: float = 0.0


@dataclass
class TeamCoreStatsDR:
    shots: int = 0
    shots_against: int = 0
    goals: int = 0
    goals_against: int = 0
    saves: int = 0
    assists: int = 0
    score: int = 0
    shooting_percentage: int = 0


@dataclass
class PlayerCoreStatsDR:
    shots: int = 0
    shots_against: int = 0
    goals: int = 0
    goals_against: int = 0
    saves: int = 0
    assists: int = 0
    score: int = 0
    mvp: bool = False
    shooting_percentage: int = 0


@dataclass
class TeamBoostStatsDR:
    bpm: int = 0
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
    amount_overfill: int = 0
    amount_overfill_stolen: int = 0
    amount_used_while_supersonic: int = 0
    time_zero_boost: float = 0.0
    time_full_boost: float = 0.0
    time_boost_0_25: float = 0.0
    time_boost_25_50: float = 0.0
    time_boost_50_75: float = 0.0
    time_boost_75_100: float = 0.0


@dataclass
class PlayerBoostStatsDR:
    bpm: int = 0
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
    amount_overfill: int = 0
    amount_overfill_stolen: int = 0
    amount_used_while_supersonic: int = 0
    time_zero_boost: float = 0.0
    percent_zero_boost: float = 0.0
    time_full_boost: float = 0.0
    percent_full_boost: float = 0.0
    time_boost_0_25: float = 0.0
    time_boost_25_50: float = 0.0
    time_boost_50_75: float = 0.0
    time_boost_75_100: float = 0.0
    percent_boost_0_25: float = 0.0
    percent_boost_25_50: float = 0.0
    percent_boost_50_75: float = 0.0
    percent_boost_75_100: float = 0.0


@dataclass
class TeamMovementStatsDR:
    total_distance: int = 0
    time_supersonic_speed: float = 0.0
    time_boost_speed: float = 0.0
    time_slow_speed: float = 0.0
    time_ground: float = 0.0
    time_low_air: float = 0.0
    time_high_air: float = 0.0
    time_powerslide: float = 0.0
    count_powerslide: int = 0


@dataclass
class PlayerMovementStatsDR:
    avg_speed: int = 0
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


@dataclass
class TeamPositioningStatsDR:
    time_defensive_third: float = 0.0
    time_neutral_third: float = 0.0
    time_offensive_third: float = 0.0
    time_defensive_half: float = 0.0
    time_offensive_half: float = 0.0
    time_behind_ball: float = 0.0
    time_infront_ball: float = 0.0


@dataclass
class PlayerPositioningStatsDR:
    avg_distance_to_ball: int = 0
    avg_distance_to_ball_possession: int = 0
    avg_distance_to_ball_no_possession: int = 0
    avg_distance_to_mates: int = 0
    time_defensive_third: float = 0.0
    time_neutral_third: float = 0.0
    time_offensive_third: float = 0.0
    time_defensive_half: float = 0.0
    time_offensive_half: float = 0.0
    time_behind_ball: float = 0.0
    time_infront_ball: float = 0.0
    time_most_back: float = 0.0
    time_most_forward: float = 0.0
    time_closest_to_ball: float = 0.0
    time_farthest_from_ball: float = 0.0
    percent_defensive_third: float = 0.0
    percent_offensive_third: float = 0.0
    percent_neutral_third: float = 0.0
    percent_defensive_half: float = 0.0
    percent_offensive_half: float = 0.0
    percent_behind_ball: float = 0.0
    percent_infront_ball: float = 0.0
    percent_most_back: float = 0.0
    percent_most_forward: float = 0.0
    percent_closest_to_ball: float = 0.0
    percent_farthest_from_ball: float = 0.0
    goals_against_while_last_defender: int = 0


@dataclass
class TeamDemoStatsDR:
    inflicted: int = 0
    taken: int = 0


@dataclass
class PlayerDemoStatsDR:
    inflicted: int = 0
    taken: int = 0


@dataclass
class TeamStatsDR(_DictToTypeMixin):
    ball: Optional[TeamBallStatsDR] = None
    core: Optional[TeamCoreStatsDR] = None
    boost: Optional[TeamBoostStatsDR] = None
    movement: Optional[TeamMovementStatsDR] = None
    positioning: Optional[TeamPositioningStatsDR] = None
    demo: Optional[TeamDemoStatsDR] = None


@dataclass
class PlayerStatsDR(_DictToTypeMixin):
    core: Optional[PlayerCoreStatsDR] = None
    boost: Optional[PlayerBoostStatsDR] = None
    movement: Optional[PlayerMovementStatsDR] = None
    positioning: Optional[PlayerPositioningStatsDR] = None
    demo: Optional[PlayerDemoStatsDR] = None


@dataclass
class PlayerDR(BasePlayer):
    # start_time: float = 0.0
    # end_time: float = 0.0
    # name: str = ""
    # id: Optional[PlayerID] = None
    # pro: bool = False
    # mvp: bool = False
    # rank: Optional[Rank] = None
    car_id: int = 0
    car_name: str = ""
    camera: Optional[CameraSettings] = None
    steering_sensitivity: float = 0
    stats: Optional[PlayerStatsDR] = None


@dataclass
class TeamDR(BaseTeam):
    # name: str = ""
    color: str = ""
    players: List[PlayerDR] = field(default_factory=list)
    stats: Optional[TeamStatsDR] = None


@dataclass
class Server:
    name: str = ""
    region: str = ""


@dataclass
class DeepReplay(BaseReplay):
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
    title: str = ""  # replay_title in shallow replay
    date_has_timezone: bool = False  # date_has_tz in shallow replay
    status: str = ""
    match_guid: str = ""
    match_type: str = ""
    team_size: int = 0
    blue: Optional[TeamDR] = None
    orange: Optional[TeamDR] = None
    server: Optional[Server] = None

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
