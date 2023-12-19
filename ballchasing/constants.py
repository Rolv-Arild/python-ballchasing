from typing import Literal, get_args, AnyStr, Union

AnyPlaylist = Union[
    AnyStr, Literal["unranked-duels", "unranked-doubles", "unranked-standard", "unranked-chaos", "private", "season",
    "offline", "local-lobby", "ranked-duels", "ranked-doubles", "ranked-solo-standard",
    "ranked-standard", "snowday", "rocketlabs", "hoops", "rumble", "tournament", "dropshot",
    "ranked-hoops", "ranked-rumble", "ranked-dropshot", "ranked-snowday", "dropshot-rumble",
    "heatseeker", "gridiron"]]


def _get_literals(type_):
    return get_args(get_args(type_)[1])


class Playlist:
    ALL = (UNRANKED_DUELS, UNRANKED_DOUBLES, UNRANKED_STANDARD, UNRANKED_CHAOS, PRIVATE, SEASON, OFFLINE, LOCAL_LOBBY,
           RANKED_DUELS, RANKED_DOUBLES, RANKED_SOLO_STANDARD, RANKED_STANDARD, SNOWDAY, ROCKETLABS, HOOPS, RUMBLE,
           TOURNAMENT, DROPSHOT, RANKED_HOOPS, RANKED_RUMBLE, RANKED_DROPSHOT, RANKED_SNOWDAY, DROPSHOT_RUMBLE,
           HEATSEEKER, GRIDIRON) = _get_literals(AnyPlaylist)
    LEGACY = (SNOWDAY, HOOPS, RUMBLE, DROPSHOT, RANKED_SOLO_STANDARD, ROCKETLABS)
    UNRANKED = (UNRANKED_DUELS, UNRANKED_DOUBLES, UNRANKED_STANDARD, UNRANKED_CHAOS)
    RANKED = (RANKED_DUELS, RANKED_DOUBLES, RANKED_STANDARD)
    LIMITED = (GRIDIRON, HEATSEEKER, DROPSHOT_RUMBLE)
    EXTRA_MODES = (RANKED_HOOPS, RANKED_RUMBLE, RANKED_DROPSHOT, RANKED_SNOWDAY)
    MISC = (PRIVATE, SEASON, OFFLINE, LOCAL_LOBBY, TOURNAMENT)


AnyRank = Union[
    AnyStr, Literal["unranked", "bronze-1", "bronze-2", "bronze-3", "silver-1", "silver-2", "silver-3", "gold-1",
    "gold-2", "gold-3", "platinum-1", "platinum-2", "platinum-3", "diamond-1", "diamond-2",
    "diamond-3", "champion-1", "champion-2", "champion-3", "grand-champion-1", "grand-champion-2",
    "grand-champion-3", "supersonic-legend"]]


class Rank:
    ALL = (UNRANKED, BRONZE_1, BRONZE_2, BRONZE_3, SILVER_1, SILVER_2, SILVER_3, GOLD_1, GOLD_2, GOLD_3, PLATINUM_1,
           PLATINUM_2, PLATINUM_3, DIAMOND_1, DIAMOND_2, DIAMOND_3, CHAMPION_1, CHAMPION_2, CHAMPION_3,
           GRAND_CHAMPION_1, GRAND_CHAMPION_2, GRAND_CHAMPION_3, SUPERSONIC_LEGEND) = _get_literals(AnyRank)
    BRONZE = (BRONZE_1, BRONZE_2, BRONZE_3)
    SILVER = (SILVER_1, SILVER_2, SILVER_3)
    GOLD = (GOLD_1, GOLD_2, GOLD_3)
    PLATINUM = (PLATINUM_1, PLATINUM_2, PLATINUM_3)
    DIAMOND = (DIAMOND_1, DIAMOND_2, DIAMOND_3)
    CHAMPION = (CHAMPION_1, CHAMPION_2, CHAMPION_3)
    GRAND_CHAMPION = (GRAND_CHAMPION_1, GRAND_CHAMPION_2, GRAND_CHAMPION_3)


AnySeason = Union[AnyStr, Literal[
    "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14",
    "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12", "f13"
]]


class Season:
    ALL = (SEASON_1, SEASON_2, SEASON_3, SEASON_4, SEASON_5, SEASON_6, SEASON_7, SEASON_8, SEASON_9, SEASON_10,
           SEASON_11, SEASON_12, SEASON_13, SEASON_14, SEASON_1_FTP, SEASON_2_FTP, SEASON_3_FTP, SEASON_4_FTP,
           SEASON_5_FTP, SEASON_6_FTP, SEASON_7_FTP, SEASON_8_FTP, SEASON_9_FTP, SEASON_10_FTP, SEASON_11_FTP,
           SEASON_12_FTP, SEASON_13_FTP) = _get_literals(AnySeason)
    PAY_TO_PLAY = (SEASON_1, SEASON_2, SEASON_3, SEASON_4, SEASON_5, SEASON_6, SEASON_7, SEASON_8, SEASON_9, SEASON_10,
                   SEASON_11, SEASON_12, SEASON_13, SEASON_14)
    FREE_TO_PLAY = (SEASON_1_FTP, SEASON_2_FTP, SEASON_3_FTP, SEASON_4_FTP, SEASON_5_FTP, SEASON_6_FTP, SEASON_7_FTP,
                    SEASON_8_FTP, SEASON_9_FTP, SEASON_10_FTP, SEASON_11_FTP, SEASON_12_FTP, SEASON_13_FTP)


AnyMatchResult = Union[AnyStr, Literal["win", "loss"]]


class MatchResult:
    WIN, LOSS = _get_literals(AnyMatchResult)


AnyReplaySortBy = Union[AnyStr, Literal["replay-date", "upload-date"]]


class ReplaySortBy:
    REPLAY_DATE, UPLOAD_DATE = _get_literals(AnyReplaySortBy)


AnyGroupSortBy = Union[AnyStr, Literal["created", "name"]]


class GroupSortBy:
    CREATED, NAME = _get_literals(AnyGroupSortBy)


AnySortDir = Union[AnyStr, Literal["asc", "desc"]]


class SortDir:
    ASCENDING, DESCENDING = ASC, DESC = _get_literals(AnySortDir)


AnyVisibility = Union[AnyStr, Literal["public", "unlisted", "private"]]


class Visibility:
    PUBLIC, UNLISTED, PRIVATE = _get_literals(AnyVisibility)


AnyPlayerIdentification = Union[AnyStr, Literal["by-id", "by-name"]]


class PlayerIdentification:
    BY_ID, BY_NAME = _get_literals(AnyPlayerIdentification)


AnyTeamIdentification = Union[AnyStr, Literal["by-distinct-players", "by-player-clusters"]]


class TeamIdentification:
    BY_DISTINCT_PLAYERS, BY_PLAYER_CLUSTERS = _get_literals(AnyTeamIdentification)


AnyMap = Union[AnyStr, Literal[
    "arc_p", "arc_darc_p", "arc_standard_p", "bb_p", "beach_night_p", "beach_p", "beachvolley", "chn_stadium_day_p",
    "chn_stadium_p", "cs_day_p", "cs_hw_p", "cs_p", "eurostadium_night_p", "eurostadium_p",
    "eurostadium_rainy_p", "eurostadium_snownight_p", "farm_night_p", "farm_p", "farm_upsidedown_p",
    "haunted_trainstation_p", "hoopsstadium_p", "labs_circlepillars_p", "labs_cosmic_p",
    "labs_cosmic_v4_p", "labs_doublegoal_p", "labs_doublegoal_v2_p", "labs_octagon_02_p",
    "labs_octagon_p", "labs_underpass_p", "labs_underpass_v0_p", "labs_utopia_p", "music_p",
    "neotokyo_p", "neotokyo_standard_p", "park_night_p", "park_p", "park_rainy_p", "shattershot_p",
    "stadium_day_p", "stadium_foggy_p", "stadium_p", "stadium_race_day_p", "stadium_winter_p",
    "throwbackstadium_p", "trainstation_dawn_p", "trainstation_night_p", "trainstation_p", "underwater_p",
    "utopiastadium_dusk_p", "utopiastadium_p", "utopiastadium_snow_p", "wasteland_night_p",
    "wasteland_night_s_p", "wasteland_p", "wasteland_s_p"]]


class Map:
    ALL = (
        ARC_P, ARC_DARC_P, ARC_STANDARD_P, BB_P, BEACH_NIGHT_P, BEACH_P, BEACHVOLLEY, CHN_STADIUM_DAY_P, CHN_STADIUM_P,
        CS_DAY_P,
        CS_HW_P, CS_P, EUROSTADIUM_NIGHT_P, EUROSTADIUM_P, EUROSTADIUM_RAINY_P, EUROSTADIUM_SNOWNIGHT_P,
        FARM_NIGHT_P, FARM_P, FARM_UPSIDEDOWN_P, HAUNTED_TRAINSTATION_P, HOOPSSTADIUM_P, LABS_CIRCLEPILLARS_P,
        LABS_COSMIC_P, LABS_COSMIC_V4_P, LABS_DOUBLEGOAL_P, LABS_DOUBLEGOAL_V2_P, LABS_OCTAGON_02_P, LABS_OCTAGON_P,
        LABS_UNDERPASS_P, LABS_UNDERPASS_V0_P, LABS_UTOPIA_P, MUSIC_P, NEOTOKYO_P, NEOTOKYO_STANDARD_P, PARK_NIGHT_P,
        PARK_P, PARK_RAINY_P, SHATTERSHOT_P, STADIUM_DAY_P, STADIUM_FOGGY_P, STADIUM_P, STADIUM_RACE_DAY_P,
        STADIUM_WINTER_P, THROWBACKSTADIUM_P, TRAINSTATION_DAWN_P, TRAINSTATION_NIGHT_P, TRAINSTATION_P,
        UNDERWATER_P, UTOPIASTADIUM_DUSK_P, UTOPIASTADIUM_P, UTOPIASTADIUM_SNOW_P, WASTELAND_NIGHT_P,
        WASTELAND_NIGHT_S_P, WASTELAND_P, WASTELAND_S_P) = _get_literals(AnyMap)
    NAMES = dict(zip(ALL, (
        "Starbase ARC", "Starbase ARC (Aftermath)", "Starbase ARC (Standard)", "Champions Field (NFL)",
        "Salty Shores (Night)",
        "Salty Shores", "Salty Shores (Volley)", "Forbidden Temple (Day)", "Forbidden Temple",
        "Champions Field (Day)", "Rivals Arena", "Champions Field", "Mannfield (Night)", "Mannfield",
        "Mannfield (Stormy)", "Mannfield (Snowy)", "Farmstead (Night)", "Farmstead",
        "Farmstead (The Upside Down)", "Urban Central (Haunted)", "Dunk House", "Pillars", "Cosmic",
        "Cosmic", "Double Goal", "Double Goal", "Octagon", "Octagon", "Underpass", "Underpass",
        "Utopia Retro", "Neon Fields", "Neo Tokyo", "Neo Tokyo (Standard)",
        "Beckwith Park (Midnight)", "Beckwith Park", "Beckwith Park (Stormy)", "Core 707",
        "DFH Stadium (Day)", "DFH Stadium (Stormy)", "DFH Stadium", "DFH Stadium (Circuit)",
        "DFH Stadium (Snowy)", "Throwback Stadium", "Urban Central (Dawn)", "Urban Central (Night)",
        "Urban Central", "Aquadome", "Utopia Coliseum (Dusk)", "Utopia Coliseum",
        "Utopia Coliseum (Snowy)", "Wasteland (Night)", "Wasteland (Standard, Night)", "Wasteland",
        "Wasteland (Standard)")))
    STANDARD_MAPS = (
        ARC_DARC_P, ARC_STANDARD_P, BEACH_NIGHT_P, CHN_STADIUM_P, CS_DAY_P, CS_P, EUROSTADIUM_NIGHT_P, EUROSTADIUM_P,
        EUROSTADIUM_RAINY_P, EUROSTADIUM_SNOWNIGHT_P, FARM_P, MUSIC_P, NEOTOKYO_STANDARD_P, PARK_NIGHT_P,
        PARK_P, PARK_RAINY_P, STADIUM_DAY_P, STADIUM_FOGGY_P, STADIUM_P, TRAINSTATION_DAWN_P,
        TRAINSTATION_NIGHT_P, TRAINSTATION_P, UNDERWATER_P, UTOPIASTADIUM_DUSK_P, UTOPIASTADIUM_P,
        WASTELAND_NIGHT_S_P, WASTELAND_S_P)
    NON_STANDARD_MAPS = (ARC_P, BB_P, BEACH_P, BEACHVOLLEY, CHN_STADIUM_DAY_P, CS_HW_P, FARM_NIGHT_P,
                         FARM_UPSIDEDOWN_P, HAUNTED_TRAINSTATION_P, HOOPSSTADIUM_P, LABS_CIRCLEPILLARS_P, LABS_COSMIC_P,
                         LABS_COSMIC_V4_P, LABS_DOUBLEGOAL_P, LABS_DOUBLEGOAL_V2_P, LABS_OCTAGON_02_P, LABS_OCTAGON_P,
                         LABS_UNDERPASS_P, LABS_UNDERPASS_V0_P, LABS_UTOPIA_P, NEOTOKYO_P, SHATTERSHOT_P,
                         STADIUM_RACE_DAY_P, STADIUM_WINTER_P, THROWBACKSTADIUM_P, UTOPIASTADIUM_SNOW_P,
                         WASTELAND_NIGHT_P, WASTELAND_P)
