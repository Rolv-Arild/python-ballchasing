"""Former home of the shared typed classes, kept for compatibility: they are generated into models.py now."""
from ballchasing.typed._base import _BaseModel, _DictToTypeMixin, model  # noqa: F401
from ballchasing.typed.models import (  # noqa: F401
    BaseGroup, BasePlayer, BaseReplay, BaseTeam, BasicGroup, PlayerId, Rank, User,
)

PlayerID = PlayerId
