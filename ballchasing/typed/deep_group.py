"""Former home of the full group classes, kept for compatibility: they are generated into models.py now."""
from ballchasing.typed.models import BaseGroup  # noqa: F401
from ballchasing.typed.models import (  # noqa: F401
    DeepGroup, Demo, GroupDuplicates, GroupPlayer, GroupPlayerAverage, GroupPlayerCore, GroupPlayerCumulative,
    GroupPlayerStats, GroupTeamAverage, GroupTeamCumulative, GroupTeamStats, PlayerBoost, PlayerMovement,
    PlayerPositioning, TeamBoost, TeamCore, TeamMovement, TeamPositioning, User,
)

CreatorDG = User
PlayerCumulativeCoreStatsDG = PlayerAverageCoreStatsDG = GroupPlayerCore
PlayerCumulativeBoostStatsDG = PlayerAverageBoostStatsDG = PlayerBoost
PlayerCumulativeMovementStatsDG = PlayerAverageMovementStatsDG = PlayerMovement
PlayerCumulativePositioningStatsDG = PlayerAveragePositioningStatsDG = PlayerPositioning
PlayerCumulativeDemoStatsDG = PlayerAverageDemoStatsDG = Demo
PlayerCumulativeStatsDG = GroupPlayerCumulative
PlayerAverageStatsDG = GroupPlayerAverage
TeamCumulativeCoreStatsDG = TeamAverageCoreStatsDG = TeamCore
TeamCumulativeBoostStatsDG = TeamAverageBoostStatsDG = TeamBoost
TeamCumulativeMovementStatsDG = TeamAverageMovementStatsDG = TeamMovement
TeamCumulativePositioningStatsDG = TeamAveragePositioningStatsDG = TeamPositioning
TeamCumulativeDemoStatsDG = TeamAverageDemoStatsDG = Demo
TeamCumulativeStatsDG = GroupTeamCumulative
TeamAverageStatsDG = GroupTeamAverage
PlayerDG = GroupPlayer
PlayerWithStatsDG = GroupPlayerStats
TeamDG = GroupTeamStats
