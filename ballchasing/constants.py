from typing import Literal, get_args, AnyStr, Union

AnyPlaylist = Union[
    AnyStr,
    Literal[
        "unranked-duels", "unranked-doubles", "unranked-standard", "unranked-chaos",
        "private", "season", "offline", "local-lobby",
        "ranked-duels", "ranked-doubles", "ranked-solo-standard", "ranked-standard",
        "snowday", "rocketlabs", "hoops", "rumble", "tournament", "dropshot",
        "ranked-hoops", "ranked-rumble", "ranked-dropshot", "ranked-snowday",
        "dropshot-rumble", "heatseeker", "gridiron", "spooky-cube"
    ]
]


def _get_literals(type_):
    return get_args(get_args(type_)[1])


class Playlist:
    ALL = (UNRANKED_DUELS, UNRANKED_DOUBLES, UNRANKED_STANDARD, UNRANKED_CHAOS, PRIVATE, SEASON, OFFLINE, LOCAL_LOBBY,
           RANKED_DUELS, RANKED_DOUBLES, RANKED_SOLO_STANDARD, RANKED_STANDARD, SNOWDAY, ROCKETLABS, HOOPS, RUMBLE,
           TOURNAMENT, DROPSHOT, RANKED_HOOPS, RANKED_RUMBLE, RANKED_DROPSHOT, RANKED_SNOWDAY, DROPSHOT_RUMBLE,
           HEATSEEKER, GRIDIRON, SPOOKY_CUBE) = _get_literals(AnyPlaylist)
    # Categories as listed on ballchasing:
    RANKED = (RANKED_DUELS, RANKED_DOUBLES, RANKED_STANDARD, RANKED_SOLO_STANDARD)
    UNRANKED = (UNRANKED_DUELS, UNRANKED_DOUBLES, UNRANKED_STANDARD, UNRANKED_CHAOS)
    EXTRA_MODES = (RANKED_HOOPS, RANKED_RUMBLE, RANKED_DROPSHOT, RANKED_SNOWDAY)
    OTHER_MODES = (SNOWDAY, ROCKETLABS, HOOPS, RUMBLE, TOURNAMENT, DROPSHOT, ROCKETLABS, DROPSHOT_RUMBLE, HEATSEEKER,
                   GRIDIRON, SPOOKY_CUBE)
    MISC = (PRIVATE, SEASON, OFFLINE, LOCAL_LOBBY)


AnyRank = Union[
    AnyStr,
    Literal[
        "unranked",
        "bronze-1", "bronze-2", "bronze-3",
        "silver-1", "silver-2", "silver-3",
        "gold-1", "gold-2", "gold-3",
        "platinum-1", "platinum-2", "platinum-3",
        "diamond-1", "diamond-2", "diamond-3",
        "champion-1", "champion-2", "champion-3",
        "grand-champion",  # Legacy. Seems to be interchangeable with "grand-champion-1"
        "grand-champion-1", "grand-champion-2", "grand-champion-3",
        "supersonic-legend"
    ],
]


class Rank:
    ALL = (
        UNRANKED,
        BRONZE_1, BRONZE_2, BRONZE_3,
        SILVER_1, SILVER_2, SILVER_3,
        GOLD_1, GOLD_2, GOLD_3,
        PLATINUM_1, PLATINUM_2, PLATINUM_3,
        DIAMOND_1, DIAMOND_2, DIAMOND_3,
        CHAMPION_1, CHAMPION_2, CHAMPION_3,
        GRAND_CHAMPION_LEGACY,
        GRAND_CHAMPION_1, GRAND_CHAMPION_2, GRAND_CHAMPION_3,
        SUPERSONIC_LEGEND
    ) = _get_literals(AnyRank)
    BRONZE = (BRONZE_1, BRONZE_2, BRONZE_3)
    SILVER = (SILVER_1, SILVER_2, SILVER_3)
    GOLD = (GOLD_1, GOLD_2, GOLD_3)
    PLATINUM = (PLATINUM_1, PLATINUM_2, PLATINUM_3)
    DIAMOND = (DIAMOND_1, DIAMOND_2, DIAMOND_3)
    CHAMPION = (CHAMPION_1, CHAMPION_2, CHAMPION_3)
    GRAND_CHAMPION = (GRAND_CHAMPION_1, GRAND_CHAMPION_2, GRAND_CHAMPION_3)


AnySeason = Union[
    AnyStr,
    Literal[
        "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14",
        "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9",
        "f10", "f11", "f12", "f13", "f14", "f15", "f16", "f17", "f18", "f19"
    ]
]


class Season:
    ALL = (
        SEASON_1_LEGACY, SEASON_2_LEGACY, SEASON_3_LEGACY, SEASON_4_LEGACY, SEASON_5_LEGACY, SEASON_6_LEGACY,
        SEASON_7_LEGACY, SEASON_8_LEGACY, SEASON_9_LEGACY, SEASON_10_LEGACY, SEASON_11_LEGACY, SEASON_12_LEGACY,
        SEASON_13_LEGACY, SEASON_14_LEGACY,
        SEASON_1_FTP, SEASON_2_FTP, SEASON_3_FTP, SEASON_4_FTP, SEASON_5_FTP, SEASON_6_FTP, SEASON_7_FTP,
        SEASON_8_FTP, SEASON_9_FTP, SEASON_10_FTP, SEASON_11_FTP, SEASON_12_FTP, SEASON_13_FTP, SEASON_14_FTP,
        SEASON_15_FTP, SEASON_16_FTP, SEASON_17_FTP, SEASON_18_FTP, SEASON_19_FTP
    ) = _get_literals(AnySeason)
    LEGACY = ALL[:14]
    FREE_TO_PLAY = ALL[14:]


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
    "arc_darc_p", "arc_p", "arc_standard_p", "bb_p", "beach_night_grs_p", "beach_night_p", "beach_p", "beachvolley",
    "chn_stadium_day_p", "chn_stadium_p", "cs_day_p", "cs_hw_p", "cs_p", "eurostadium_dusk_p", "eurostadium_night_p",
    "eurostadium_p", "eurostadium_rainy_p", "eurostadium_snownight_p", "farm_grs_p", "farm_hw_p", "farm_night_p",
    "farm_p", "farm_upsidedown_p", "ff_dusk_p", "fni_stadium_p", "haunted_trainstation_p", "hoopsstadium_p",
    "hoopsstreet_p", "ko_calavera_p", "ko_carbon_p", "ko_quadron_p", "labs_basin_p", "labs_circlepillars_p",
    "labs_corridor_p", "labs_cosmic_p", "labs_cosmic_v4_p", "labs_doublegoal_p", "labs_doublegoal_v2_p",
    "labs_galleon_mast_p", "labs_galleon_p", "labs_holyfield_p", "labs_holyfield_space_p", "labs_octagon_02_p",
    "labs_octagon_p", "labs_pillarglass_p", "labs_pillarheat_p", "labs_pillarwings_p", "labs_underpass_p",
    "labs_underpass_v0_p", "labs_utopia_p", "music_p", "neotokyo_arcade_p", "neotokyo_hax_p", "neotokyo_p",
    "neotokyo_standard_p", "neotokyo_toon_p", "outlaw_oasis_p", "outlaw_p", "park_bman_p", "park_night_p", "park_p",
    "park_rainy_p", "park_snowy_p", "shattershot_p", "stadium_10a_p", "stadium_day_p", "stadium_foggy_p", "stadium_p",
    "stadium_race_day_p", "stadium_winter_p", "street_p", "swoosh_p", "throwbackhockey_p", "throwbackstadium_p",
    "trainstation_dawn_p", "trainstation_night_p", "trainstation_p", "trainstation_spooky_p", "uf_day_p",
    "underwater_grs_p", "underwater_p", "utopiastadium_dusk_p", "utopiastadium_lux_p", "utopiastadium_p",
    "utopiastadium_snow_p", "wasteland_grs_p", "wasteland_night_p", "wasteland_night_s_p", "wasteland_p",
    "wasteland_s_p", "woods_night_p", "woods_p"
]]


class Map:
    ALL = (
        ARC_DARC_P, ARC_P, ARC_STANDARD_P, BB_P, BEACH_NIGHT_GRS_P, BEACH_NIGHT_P, BEACH_P, BEACHVOLLEY,
        CHN_STADIUM_DAY_P, CHN_STADIUM_P, CS_DAY_P, CS_HW_P, CS_P, EUROSTADIUM_DUSK_P, EUROSTADIUM_NIGHT_P,
        EUROSTADIUM_P, EUROSTADIUM_RAINY_P, EUROSTADIUM_SNOWNIGHT_P, FARM_GRS_P, FARM_HW_P, FARM_NIGHT_P, FARM_P,
        FARM_UPSIDEDOWN_P, FF_DUSK_P, FNI_STADIUM_P, HAUNTED_TRAINSTATION_P, HOOPSSTADIUM_P, HOOPSSTREET_P,
        KO_CALAVERA_P, KO_CARBON_P, KO_QUADRON_P, LABS_BASIN_P, LABS_CIRCLEPILLARS_P, LABS_CORRIDOR_P, LABS_COSMIC_P,
        LABS_COSMIC_V4_P, LABS_DOUBLEGOAL_P, LABS_DOUBLEGOAL_V2_P, LABS_GALLEON_MAST_P, LABS_GALLEON_P,
        LABS_HOLYFIELD_P, LABS_HOLYFIELD_SPACE_P, LABS_OCTAGON_02_P, LABS_OCTAGON_P, LABS_PILLARGLASS_P,
        LABS_PILLARHEAT_P, LABS_PILLARWINGS_P, LABS_UNDERPASS_P, LABS_UNDERPASS_V0_P, LABS_UTOPIA_P, MUSIC_P,
        NEOTOKYO_ARCADE_P, NEOTOKYO_HAX_P, NEOTOKYO_P, NEOTOKYO_STANDARD_P, NEOTOKYO_TOON_P, OUTLAW_OASIS_P, OUTLAW_P,
        PARK_BMAN_P, PARK_NIGHT_P, PARK_P, PARK_RAINY_P, PARK_SNOWY_P, SHATTERSHOT_P, STADIUM_10A_P, STADIUM_DAY_P,
        STADIUM_FOGGY_P, STADIUM_P, STADIUM_RACE_DAY_P, STADIUM_WINTER_P, STREET_P, SWOOSH_P, THROWBACKHOCKEY_P,
        THROWBACKSTADIUM_P, TRAINSTATION_DAWN_P, TRAINSTATION_NIGHT_P, TRAINSTATION_P, TRAINSTATION_SPOOKY_P, UF_DAY_P,
        UNDERWATER_GRS_P, UNDERWATER_P, UTOPIASTADIUM_DUSK_P, UTOPIASTADIUM_LUX_P, UTOPIASTADIUM_P,
        UTOPIASTADIUM_SNOW_P, WASTELAND_GRS_P, WASTELAND_NIGHT_P, WASTELAND_NIGHT_S_P, WASTELAND_P, WASTELAND_S_P,
        WOODS_NIGHT_P, WOODS_P
    ) = _get_literals(AnyMap)
    NAMES = (
        "Starbase ARC (Aftermath)", "Starbase ARC", "Starbase ARC (Standard)", "Champions Field (NFL)",
        "Salty Shores (Salty Fest)", "Salty Shores (Night)", "Salty Shores", "Salty Shores (Volley)",
        "Forbidden Temple (Day)", "Forbidden Temple", "Champions Field (Day)", "Rivals Arena", "Champions Field",
        "Mannfield (Dusk)", "Mannfield (Night)", "Mannfield", "Mannfield (Stormy)", "Mannfield (Snowy)",
        "Farmstead (Pitched)", "Farmstead (Spooky)", "Farmstead (Night)", "Farmstead", "Farmstead (The Upside Down)",
        "Estadio Vida (Dusk)", "Forbidden Temple (Fire & Ice)", "Urban Central (Haunted)", "Dunk House",
        "The Block (Dusk)", "Calavera", "Carbon", "Quadron", "Basin", "Pillars", "Corridor", "Cosmic", "Cosmic",
        "Double Goal", "Double Goal", "Galleon Retro", "Galleon", "Loophole", "Holyfield", "Octagon", "Octagon",
        "Hourglass", "Barricade", "Colossus", "Underpass", "Underpass", "Utopia Retro", "Neon Fields",
        "Neo Tokyo (Arcade)", "Neo Tokyo (Hacked)", "Neo Tokyo", "Neo Tokyo (Standard)", "Neo Tokyo (Comic)",
        "Deadeye Canyon (Oasis)", "Deadeye Canyon", "Beckwith Park (Night)", "Beckwith Park (Midnight)",
        "Beckwith Park", "Beckwith Park (Stormy)", "Beckwith Park (Snowy)", "Core 707",
        "DFH Stadium (10th Anniversary)", "DFH Stadium (Day)", "DFH Stadium (Stormy)", "DFH Stadium",
        "DFH Stadium (Circuit)", "DFH Stadium (Snowy)", "Sovereign Heights (Dusk)", "Champions Field (Nike FC)",
        "Throwback Stadium (Snowy)", "Throwback Stadium", "Urban Central (Dawn)", "Urban Central (Night)",
        "Urban Central", "Urban Central (Spooky)", "Futura Garden", "AquaDome (Salty Shallows)", "Aquadome",
        "Utopia Coliseum (Dusk)", "Utopia Coliseum (Gilded)", "Utopia Coliseum", "Utopia Coliseum (Snowy)",
        "Wasteland (Pitched)", "Wasteland (Night)", "Wasteland (Standard, Night)", "Wasteland", "Wasteland (Standard)",
        "Drift Woods (Night)", "Drift Woods"
    )
    CODE_TO_NAME = {code: name for code, name in zip(ALL, NAMES)}
    STANDARD_MAPS = (
        ARC_DARC_P, ARC_STANDARD_P, BEACH_NIGHT_GRS_P, BEACH_NIGHT_P, BEACH_P, CHN_STADIUM_DAY_P, CHN_STADIUM_P,
        CS_DAY_P, CS_HW_P, CS_P, EUROSTADIUM_DUSK_P, EUROSTADIUM_NIGHT_P, EUROSTADIUM_P, EUROSTADIUM_RAINY_P,
        EUROSTADIUM_SNOWNIGHT_P, FARM_GRS_P, FARM_NIGHT_P, FARM_P, FARM_UPSIDEDOWN_P, FF_DUSK_P, FNI_STADIUM_P, MUSIC_P,
        NEOTOKYO_ARCADE_P, NEOTOKYO_HAX_P, NEOTOKYO_STANDARD_P, OUTLAW_OASIS_P, OUTLAW_P, PARK_NIGHT_P, PARK_P,
        PARK_RAINY_P, PARK_SNOWY_P, STADIUM_10A_P, STADIUM_DAY_P, STADIUM_FOGGY_P, STADIUM_P, STADIUM_RACE_DAY_P,
        STADIUM_WINTER_P, STREET_P, TRAINSTATION_DAWN_P, TRAINSTATION_NIGHT_P, TRAINSTATION_P, UF_DAY_P,
        UNDERWATER_GRS_P, UNDERWATER_P, UTOPIASTADIUM_DUSK_P, UTOPIASTADIUM_LUX_P, UTOPIASTADIUM_P,
        UTOPIASTADIUM_SNOW_P, WASTELAND_GRS_P, WASTELAND_NIGHT_P, WASTELAND_NIGHT_S_P, WASTELAND_P, WASTELAND_S_P,
        WOODS_NIGHT_P, WOODS_P
    )
    NON_STANDARD_MAPS = (
        ARC_P, BB_P, BEACHVOLLEY, FARM_HW_P, HAUNTED_TRAINSTATION_P, HOOPSSTADIUM_P, HOOPSSTREET_P, KO_CALAVERA_P,
        KO_CARBON_P, KO_QUADRON_P, LABS_BASIN_P, LABS_CIRCLEPILLARS_P, LABS_CORRIDOR_P, LABS_COSMIC_P, LABS_COSMIC_V4_P,
        LABS_DOUBLEGOAL_P, LABS_DOUBLEGOAL_V2_P, LABS_GALLEON_MAST_P, LABS_GALLEON_P, LABS_HOLYFIELD_P,
        LABS_HOLYFIELD_SPACE_P, LABS_OCTAGON_02_P, LABS_OCTAGON_P, LABS_PILLARGLASS_P, LABS_PILLARHEAT_P,
        LABS_PILLARWINGS_P, LABS_UNDERPASS_P, LABS_UNDERPASS_V0_P, LABS_UTOPIA_P, NEOTOKYO_P, NEOTOKYO_TOON_P,
        PARK_BMAN_P, SHATTERSHOT_P, SWOOSH_P, THROWBACKHOCKEY_P, THROWBACKSTADIUM_P, TRAINSTATION_SPOOKY_P
    )
