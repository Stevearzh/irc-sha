"""装备牌：武器 / 防具 / +1 马 / -1 马。

共用结算逻辑（置入槽位、替换旧装备）在 isha.card.base.EquipRule；
武器特效（青龙追杀、贯石斧强命等）见 card/common/sha.py 与
card/base.py 的 dodge_window；丈八蛇矛见 weapon.ZhangbaRule。
"""

from .armor import ArmorRule
from .horse import MinusHorseRule, PlusHorseRule
from .weapon import WEAPON_NAMES, WeaponRule, ZhangbaRule

__all__ = ['ArmorRule', 'MinusHorseRule', 'PlusHorseRule',
           'WEAPON_NAMES', 'WeaponRule', 'ZhangbaRule']
