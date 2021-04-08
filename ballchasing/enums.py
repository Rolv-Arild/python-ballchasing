import warnings
from enum import Enum


class _Checkable:
    @classmethod
    def check(cls, val):
        if val is None:
            return None
        return cls(val).value


class Playlist(_Checkable, Enum):
    UNRANKED_DUELS = "unranked-duels"
    UNRANKED_DOUBLES = "unranked-doubles"
    UNRANKED_STANDARD = "unranked-standard"
    UNRANKED_CHAOS = "unranked-chaos"
    PRIVATE = "private"
    SEASON = "season"
    OFFLINE = "offline"
    RANKED_DUELS = "ranked-duels"
    RANKED_DOUBLES = "ranked-doubles"
    RANKED_SOLO_STANDARD = "ranked-solo-standard"
    RANKED_STANDARD = "ranked-standard"
    SNOWDAY = "snowday"
    ROCKETLABS = "rocketlabs"
    HOOPS = "hoops"
    RUMBLE = "rumble"
    TOURNAMENT = "tournament"
    DROPSHOT = "dropshot"
    RANKED_HOOPS = "ranked-hoops"
    RANKED_RUMBLE = "ranked-rumble"
    RANKED_DROPSHOT = "ranked-dropshot"
    RANKED_SNOWDAY = "ranked-snowday"
    DROPSHOT_RUMBLE = "dropshot-rumble"
    HEATSEEKER = "heatseeker"


class Rank(_Checkable, Enum):
    UNRANKED = "unranked"
    BRONZE_1 = "bronze-1"
    BRONZE_2 = "bronze-2"
    BRONZE_3 = "bronze-3"
    SILVER_1 = "silver-1"
    SILVER_2 = "silver-2"
    SILVER_3 = "silver-3"
    GOLD_1 = "gold-1"
    GOLD_2 = "gold-2"
    GOLD_3 = "gold-3"
    PLATINUM_1 = "platinum-1"
    PLATINUM_2 = "platinum-2"
    PLATINUM_3 = "platinum-3"
    DIAMOND_1 = "diamond-1"
    DIAMOND_2 = "diamond-2"
    DIAMOND_3 = "diamond-3"
    CHAMPION_1 = "champion-1"
    CHAMPION_2 = "champion-2"
    CHAMPION_3 = "champion-3"
    GRAND_CHAMPION_1 = "grand-champion-1"
    GRAND_CHAMPION_2 = "grand-champion-2"
    GRAND_CHAMPION_3 = "grand-champion-3"
    SUPERSONIC_LEGEND = "supersonic-legend"


class MatchResult(_Checkable, Enum):
    WIN = "win"
    LOSS = "loss"


class ReplaySortBy(_Checkable, Enum):
    REPLAY_DATE = "replay-date"
    UPLOAD_DATE = "upload-date"


class GroupSortBy(_Checkable, Enum):
    CREATED = "created"
    NAME = "name"


class SortDir(_Checkable, Enum):
    ASCENDING = ASC = "asc"
    DESCENDING = DESC = "desc"


class Visibility(_Checkable, Enum):
    PUBLIC = "public"
    UNLISTED = "unlisted"
    PRIVATE = "private"


class PlayerIdentification(_Checkable, Enum):
    BY_ID = "by-id"
    BY_NAME = "by-name"


class TeamIdentification(_Checkable, Enum):
    BY_DISTINCT_PLAYERS = "by-distinct-players"
    BY_PLAYER_CLUSTERS = "by-player-clusters"


class Map(_Checkable, Enum):
    ARC_P = "arc_p", "Starbase ARC"
    ARC_STANDARD_P = "arc_standard_p", "Starbase ARC (Standard)"
    BB_P = "bb_p", "Champions Field (NFL)"
    BEACH_NIGHT_P = "beach_night_p", "Salty Shores (Night)"
    BEACH_P = "beach_p", "Salty Shores"
    BEACHVOLLEY = "beachvolley", "Salty Shores (Volley)"
    CHN_STADIUM_DAY_P = "chn_stadium_day_p", "Forbidden Temple (Day)"
    CHN_STADIUM_P = "chn_stadium_p", "Forbidden Temple"
    CS_DAY_P = "cs_day_p", "Champions Field (Day)"
    CS_HW_P = "cs_hw_p", "Rivals Arena"
    CS_P = "cs_p", "Champions Field"
    EUROSTADIUM_NIGHT_P = "eurostadium_night_p", "Mannfield (Night)"
    EUROSTADIUM_P = "eurostadium_p", "Mannfield"
    EUROSTADIUM_RAINY_P = "eurostadium_rainy_p", "Mannfield (Stormy)"
    EUROSTADIUM_SNOWNIGHT_P = "eurostadium_snownight_p", "Mannfield (Snowy)"
    FARM_NIGHT_P = "farm_night_p", "Farmstead (Night)"
    FARM_P = "farm_p", "Farmstead"
    FARM_UPSIDEDOWN_P = "farm_upsidedown_p", "Farmstead (The Upside Down)"
    HAUNTED_TRAINSTATION_P = "haunted_trainstation_p", "Urban Central (Haunted)"
    HOOPSSTADIUM_P = "hoopsstadium_p", "Dunk House"
    LABS_CIRCLEPILLARS_P = "labs_circlepillars_p", "Pillars"
    LABS_COSMIC_P = "labs_cosmic_p", "Cosmic"
    LABS_COSMIC_V4_P = "labs_cosmic_v4_p", "Cosmic"
    LABS_DOUBLEGOAL_P = "labs_doublegoal_p", "Double Goal"
    LABS_DOUBLEGOAL_V2_P = "labs_doublegoal_v2_p", "Double Goal"
    LABS_OCTAGON_02_P = "labs_octagon_02_p", "Octagon"
    LABS_OCTAGON_P = "labs_octagon_p", "Octagon"
    LABS_UNDERPASS_P = "labs_underpass_p", "Underpass"
    LABS_UNDERPASS_V0_P = "labs_underpass_v0_p", "Underpass"
    LABS_UTOPIA_P = "labs_utopia_p", "Utopia Retro"
    MUSIC_P = "music_p", "Neon Fields"
    NEOTOKYO_P = "neotokyo_p", "Neo Tokyo"
    NEOTOKYO_STANDARD_P = "neotokyo_standard_p", "Neo Tokyo (Standard)"
    PARK_NIGHT_P = "park_night_p", "Beckwith Park (Midnight)"
    PARK_P = "park_p", "Beckwith Park"
    PARK_RAINY_P = "park_rainy_p", "Beckwith Park (Stormy)"
    SHATTERSHOT_P = "shattershot_p", "Core 707"
    STADIUM_DAY_P = "stadium_day_p", "DFH Stadium (Day)"
    STADIUM_FOGGY_P = "stadium_foggy_p", "DFH Stadium (Stormy)"
    STADIUM_P = "stadium_p", "DFH Stadium"
    STADIUM_WINTER_P = "stadium_winter_p", "DFH Stadium (Snowy)"
    THROWBACKSTADIUM_P = "throwbackstadium_p", "Throwback Stadium"
    TRAINSTATION_DAWN_P = "trainstation_dawn_p", "Urban Central (Dawn)"
    TRAINSTATION_NIGHT_P = "trainstation_night_p", "Urban Central (Night)"
    TRAINSTATION_P = "trainstation_p", "Urban Central"
    UNDERWATER_P = "underwater_p", "Aquadome"
    UTOPIASTADIUM_DUSK_P = "utopiastadium_dusk_p", "Utopia Coliseum (Dusk)"
    UTOPIASTADIUM_P = "utopiastadium_p", "Utopia Coliseum"
    UTOPIASTADIUM_SNOW_P = "utopiastadium_snow_p", "Utopia Coliseum (Snowy)"
    WASTELAND_NIGHT_P = "wasteland_night_p", "Wasteland (Night)"
    WASTELAND_NIGHT_S_P = "wasteland_night_s_p", "Wasteland (Standard, Night)"
    WASTELAND_P = "wasteland_p", "Wasteland"
    WASTELAND_S_P = "wasteland_s_p", "Wasteland (Standard)"
