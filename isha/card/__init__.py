"""卡牌规则：基本牌 + 锦囊 + 装备（标准包 104 张 + EX 包 4 张）。

每张牌一个文件，按种类分目录：
    common/  基本牌（杀、闪、桃）
    trick/   锦囊牌（aoe.py、raid.py 为同族锦囊的共用基类）
    equip/   装备牌（武器、防具、坐骑）
共享常量、闪避窗口与锦囊/装备基类在 base.py。
"""

from isha.dict.card import CARD_NAME, MINUS_HORSES, PLUS_HORSES

from .common import PeachRule, ShaRule, ShanRule
from .equip import (WEAPON_NAMES, ArmorRule, MinusHorseRule, PlusHorseRule,
                    WeaponRule, ZhangbaRule)
from .trick import (ArrowsRule, BorrowSwordRule, ContentmentRule,
                    DismantleRule, DuelRule, ExNihiloRule, GardenRule,
                    HarvestRule, LightningRule, NegateRule, SavageRule,
                    SnatchRule)

RULES = [
    ShaRule(), ShanRule(), PeachRule(),
    NegateRule(),
    DuelRule(), SavageRule(), ArrowsRule(),
    SnatchRule(), DismantleRule(),
    ExNihiloRule(), GardenRule(), HarvestRule(),
    ContentmentRule(), LightningRule(),
    BorrowSwordRule(),
    *[WeaponRule(n) for n in WEAPON_NAMES],
    ZhangbaRule(),
    ArmorRule(CARD_NAME['bagua']),
    ArmorRule(CARD_NAME['renwang']),
    *[PlusHorseRule(n) for n in PLUS_HORSES],
    *[MinusHorseRule(n) for n in MINUS_HORSES],
]

DEFAULT_RULES = {r.name: r for r in RULES}
DEFAULT_CARD_TYPES = {r.name: r.type for r in RULES}
