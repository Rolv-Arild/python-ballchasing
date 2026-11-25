"""Former home of the replay list classes, kept for compatibility: they are generated into models.py now."""
from ballchasing.typed.models import BasePlayer, BaseReplay, BaseTeam  # noqa: F401
from ballchasing.typed.models import ReplaySummaryPlayer, ReplaySummaryTeam, ShallowReplay  # noqa: F401

PlayerSR = ReplaySummaryPlayer
TeamSR = ReplaySummaryTeam
