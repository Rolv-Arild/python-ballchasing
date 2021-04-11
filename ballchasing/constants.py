from typing import Literal, Union, Sequence, get_args

AnyPlaylist = Literal["unranked-duels", "unranked-doubles", "unranked-standard", "unranked-chaos", "private", "season",
                      "offline", "local-lobby", "ranked-duels", "ranked-doubles", "ranked-solo-standard",
                      "ranked-standard", "snowday", "rocketlabs", "hoops", "rumble", "tournament", "dropshot",
                      "ranked-hoops", "ranked-rumble", "ranked-dropshot", "ranked-snowday", "dropshot-rumble",
                      "heatseeker", "gridiron"]


class Playlist:
    ALL = (UNRANKED_DUELS, UNRANKED_DOUBLES, UNRANKED_STANDARD, UNRANKED_CHAOS, PRIVATE, SEASON, OFFLINE, LOCAL_LOBBY,
           RANKED_DUELS, RANKED_DOUBLES, RANKED_SOLO_STANDARD, RANKED_STANDARD, SNOWDAY, ROCKETLABS, HOOPS, RUMBLE,
           TOURNAMENT, DROPSHOT, RANKED_HOOPS, RANKED_RUMBLE, RANKED_DROPSHOT, RANKED_SNOWDAY, DROPSHOT_RUMBLE,
           HEATSEEKER, GRIDIRON) = get_args(AnyPlaylist)


AnyRank = Literal["unranked", "bronze-1", "bronze-2", "bronze-3", "silver-1", "silver-2", "silver-3", "gold-1",
                  "gold-2", "gold-3", "platinum-1", "platinum-2", "platinum-3", "diamond-1", "diamond-2",
                  "diamond-3", "champion-1", "champion-2", "champion-3", "grand-champion-1", "grand-champion-2",
                  "grand-champion-3", "supersonic-legend"]


class Rank:
    ALL = (UNRANKED, BRONZE_1, BRONZE_2, BRONZE_3, SILVER_1, SILVER_2, SILVER_3, GOLD_1, GOLD_2, GOLD_3, PLATINUM_1,
           PLATINUM_2, PLATINUM_3, DIAMOND_1, DIAMOND_2, DIAMOND_3, CHAMPION_1, CHAMPION_2, CHAMPION_3,
           GRAND_CHAMPION_1, GRAND_CHAMPION_2, GRAND_CHAMPION_3, SUPERSONIC_LEGEND) = get_args(AnyRank)


AnySeason = Literal["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "f1", "f2", "f3"]


class Season:
    ALL = (
        SEASON_1, SEASON_2, SEASON_3, SEASON_4, SEASON_5, SEASON_6, SEASON_7, SEASON_8, SEASON_9, SEASON_10, SEASON_11,
        SEASON_12, SEASON_13, SEASON_14, SEASON_1_FTP, SEASON_2_FTP, SEASON_3_FTP) = get_args(AnySeason)


AnyMatchResult = Literal["win", "loss"]


class MatchResult:
    WIN, LOSS = get_args(AnyMatchResult)


AnyReplaySortBy = Literal["replay-date", "upload-date"]


class ReplaySortBy:
    REPLAY_DATE, UPLOAD_DATE = get_args(AnyReplaySortBy)


AnyGroupSortBy = Literal["created", "name"]


class GroupSortBy:
    CREATED, NAME = get_args(AnyGroupSortBy)


AnySortDir = Literal["asc", "desc"]


class SortDir:
    ASCENDING, DESCENDING = ASC, DESC = get_args(AnySortDir)


AnyVisibility = Literal["public", "unlisted", "private"]


class Visibility:
    PUBLIC, UNLISTED, PRIVATE = get_args(AnyVisibility)


AnyPlayerIdentification = Literal["by-id", "by-name"]


class PlayerIdentification:
    BY_ID, BY_NAME = get_args(AnyPlayerIdentification)


AnyTeamIdentification = Literal["by-distinct-players", "by-player-clusters"]


class TeamIdentification:
    BY_DISTINCT_PLAYERS, BY_PLAYER_CLUSTERS = get_args(AnyTeamIdentification)


AnyMap = Literal["arc_p", "arc_standard_p", "bb_p", "beach_night_p", "beach_p", "beachvolley", "chn_stadium_day_p",
                 "chn_stadium_p", "cs_day_p", "cs_hw_p", "cs_p", "eurostadium_night_p", "eurostadium_p",
                 "eurostadium_rainy_p", "eurostadium_snownight_p", "farm_night_p", "farm_p", "farm_upsidedown_p",
                 "haunted_trainstation_p", "hoopsstadium_p", "labs_circlepillars_p", "labs_cosmic_p",
                 "labs_cosmic_v4_p", "labs_doublegoal_p", "labs_doublegoal_v2_p", "labs_octagon_02_p",
                 "labs_octagon_p", "labs_underpass_p", "labs_underpass_v0_p", "labs_utopia_p", "music_p",
                 "neotokyo_p", "neotokyo_standard_p", "park_night_p", "park_p", "park_rainy_p", "shattershot_p",
                 "stadium_day_p", "stadium_foggy_p", "stadium_p", "stadium_race_day_p", "stadium_winter_p",
                 "throwbackstadium_p", "trainstation_dawn_p", "trainstation_night_p", "trainstation_p", "underwater_p",
                 "utopiastadium_dusk_p", "utopiastadium_p", "utopiastadium_snow_p", "wasteland_night_p",
                 "wasteland_night_s_p", "wasteland_p", "wasteland_s_p"]


class Map:
    ALL = (ARC_P, ARC_STANDARD_P, BB_P, BEACH_NIGHT_P, BEACH_P, BEACHVOLLEY, CHN_STADIUM_DAY_P, CHN_STADIUM_P, CS_DAY_P,
           CS_HW_P, CS_P, EUROSTADIUM_NIGHT_P, EUROSTADIUM_P, EUROSTADIUM_RAINY_P, EUROSTADIUM_SNOWNIGHT_P,
           FARM_NIGHT_P, FARM_P, FARM_UPSIDEDOWN_P, HAUNTED_TRAINSTATION_P, HOOPSSTADIUM_P, LABS_CIRCLEPILLARS_P,
           LABS_COSMIC_P, LABS_COSMIC_V4_P, LABS_DOUBLEGOAL_P, LABS_DOUBLEGOAL_V2_P, LABS_OCTAGON_02_P, LABS_OCTAGON_P,
           LABS_UNDERPASS_P, LABS_UNDERPASS_V0_P, LABS_UTOPIA_P, MUSIC_P, NEOTOKYO_P, NEOTOKYO_STANDARD_P, PARK_NIGHT_P,
           PARK_P, PARK_RAINY_P, SHATTERSHOT_P, STADIUM_DAY_P, STADIUM_FOGGY_P, STADIUM_P, STADIUM_RACE_DAY_P,
           STADIUM_WINTER_P, THROWBACKSTADIUM_P, TRAINSTATION_DAWN_P, TRAINSTATION_NIGHT_P, TRAINSTATION_P,
           UNDERWATER_P, UTOPIASTADIUM_DUSK_P, UTOPIASTADIUM_P, UTOPIASTADIUM_SNOW_P, WASTELAND_NIGHT_P,
           WASTELAND_NIGHT_S_P, WASTELAND_P, WASTELAND_S_P) = get_args(AnyMap)
