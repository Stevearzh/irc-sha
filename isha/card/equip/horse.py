"""坐骑：+1 马（防御：别人算到我的距离 +1）与 -1 马（进攻：我算到别人的距离 -1）。

距离计算见 engine.distance。
"""

from ..base import EquipRule


class PlusHorseRule(EquipRule):
    slot = 'plus_horse'


class MinusHorseRule(EquipRule):
    slot = 'minus_horse'
