"""武器：置入武器槽，提供攻击范围（牌名括号中的 spec）。

各武器特效见 card/common/sha.py（诸葛连弩、贯石斧、青龙偃月刀、
麒麟弓、寒冰剑；仁王盾判定也在其中）与 card/base.py 的
dodge_window / ignores_armor（青釭剑）；丈八蛇矛（两张手牌当杀）
由下方 ZhangbaRule 经 EquipRule 的出牌阶段额外选项钩子
（play_extra / check_extra / resolve_extra）实现。
"""

from isha.core.actions import PlayCards
from isha.core.engine import Frame
from isha.dict.card import CARD_COLOR, CARD_NAME

from ..base import EquipRule


class WeaponRule(EquipRule):
    slot = 'weapon'


class ZhangbaRule(WeaponRule):
    """丈八蛇矛：出牌阶段可将两张手牌当杀使用（虚拟杀，复用杀的结算帧）。"""

    extra_key = 'zhangba'

    def __init__(self):
        super().__init__(CARD_NAME['zhangba'])

    def play_extra(self, eng, p):
        if p.used_sha or len(p.hand) < 2:
            return None
        return eng.rules[eng.sha_card].play_targets(eng, p, None) or None

    def check_extra(self, p, action, targets) -> bool:
        if not isinstance(action, PlayCards) or len(action.cids) != 2:
            return False
        c1, c2 = action.cids
        return (c1 != c2 and p.find(c1) is not None and p.find(c2) is not None
                and action.target in targets)

    def resolve_extra(self, eng, p, action) -> Frame:
        cards = [eng.play_card(p, cid) for cid in action.cids]
        p.used_sha = True
        label = '+'.join(c.label for c in cards)
        # 虚拟杀的颜色：两牌同色取该色，异色则为无色（仁王盾只挡黑杀）
        colors = {c.color for c in cards}
        color = colors.pop() if len(colors) == 1 else CARD_COLOR['no_color']
        eng.emit('card_used', nick=p.nick, target=action.target,
                 label=f'{self.name}[{label}]当杀')
        yield from eng.rules[eng.sha_card].sha_effect(
            eng, p, eng.player(action.target), label, color)


WEAPON_NAMES = [CARD_NAME[k] for k in
                ('zhuge', 'gender_sword', 'qinggang', 'qinglong',
                 'guanshi', 'fangtian', 'qilin', 'icesword')]
