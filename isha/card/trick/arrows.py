"""万箭齐发：其余角色需打出闪（或八卦阵判定），否则受到 1 点伤害。"""

from isha.dict.card import CARD_NAME

from ..base import SHAN
from .aoe import AoeRule


class ArrowsRule(AoeRule):
    name = CARD_NAME['arrows']
    response_name = SHAN
