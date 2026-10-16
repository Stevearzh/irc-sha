"""南蛮入侵：其余角色需打出杀，否则受到 1 点伤害。"""

from isha.dict.card import CARD_NAME

from ..base import SHA
from .aoe import AoeRule


class SavageRule(AoeRule):
    name = CARD_NAME['savage']
    response_name = SHA
