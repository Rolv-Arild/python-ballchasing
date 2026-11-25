from typing import Optional

from ballchasing.typed.shared import User, BaseGroup, model


@model
class ShallowGroup(BaseGroup):
    # id: str = ""
    # link: str = ""
    # name: str = ""
    # created: Optional[datetime] = None
    # player_identification: str = ""
    # team_identification: str = ""
    # shared: bool = False
    direct_replays: int = 0
    indirect_replays: int = 0
    user: Optional[User] = None
