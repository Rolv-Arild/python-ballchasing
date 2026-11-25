"""Former home of the full replay classes, kept for compatibility: they are generated into models.py now."""
from ballchasing.typed.models import BasePlayer, BaseReplay, BaseTeam  # noqa: F401
from ballchasing.typed.models import (  # noqa: F401
    Camera, DeepReplay, Demo, PlayerBoost, PlayerCore, PlayerMovement, PlayerPositioning, PlayerStats, ReplayPlayer,
    ReplayTeam, Server, TeamBall, TeamBoost, TeamCore, TeamMovement, TeamPositioning, TeamStats,
)

CameraSettings = Camera
TeamBallStatsDR = TeamBall
TeamCoreStatsDR = TeamCore
PlayerCoreStatsDR = PlayerCore
TeamBoostStatsDR = TeamBoost
PlayerBoostStatsDR = PlayerBoost
TeamMovementStatsDR = TeamMovement
PlayerMovementStatsDR = PlayerMovement
TeamPositioningStatsDR = TeamPositioning
PlayerPositioningStatsDR = PlayerPositioning
TeamDemoStatsDR = Demo
PlayerDemoStatsDR = Demo
TeamStatsDR = TeamStats
PlayerStatsDR = PlayerStats
PlayerDR = ReplayPlayer
TeamDR = ReplayTeam
