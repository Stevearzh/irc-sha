"""卡牌规则共享基础：牌名/类型常量、辅助函数、闪避窗口、锦囊与装备基类。

每张牌的规则 = 能否主动使用（play_targets，返回 None 表示不可出）+
结算（resolve）：需要交互时返回结算帧（生成器），可同步完成时返回 None。
延时锦囊额外实现 judge()：判定阶段的结算帧。
"""

from isha.core.actions import PlayCards
from isha.core.engine import Frame
from isha.dict.card import CARD_COLOR, CARD_NAME, CARD_TYPE

SHA = CARD_NAME['sha']
SHAN = CARD_NAME['shan']
PEACH = CARD_NAME['peach']
NEGATE = CARD_NAME['negate']
ZHUGE = CARD_NAME['zhuge']
QINGGANG = CARD_NAME['qinggang']
QINGLONG = CARD_NAME['qinglong']
GUANSHI = CARD_NAME['guanshi']
QILIN = CARD_NAME['qilin']
FANGTIAN = CARD_NAME['fangtian']
BAGUA = CARD_NAME['bagua']
ICESWORD = CARD_NAME['icesword']
RENWANG = CARD_NAME['renwang']

TRICK = CARD_TYPE['trick']
BASIC = CARD_TYPE['basic']
EQUIP = CARD_TYPE['equip']


def others(eng, p):
    """除 p 以外的存活玩家 nick 列表。"""
    return [q.nick for q in eng.alive() if q is not p]


def ignores_armor(source) -> bool:
    """青釭剑持有者的杀无视目标防具（八卦阵、仁王盾）。"""
    return source is not None and source.weapon is not None \
        and source.weapon.name == QINGGANG


def dodge_window(eng, source, target, label) -> Frame:
    """杀/万箭的闪避窗口：打出闪，或八卦阵判定（青釭剑无视八卦阵）。

    每次响应至多判定一次八卦阵；判定为黑仍需出闪或放弃。
    返回是否闪避成功。
    """
    armor_ok = target.armor is not None and target.armor.name == BAGUA \
        and not ignores_armor(source)
    while True:
        shans = [c for c in target.hand if c.name == SHAN]
        if not shans and not armor_ok:
            return False
        act = yield eng.card_response_ask(
            target.nick, 'respond_sha', shans,
            {'source': source.nick if source else None, 'sha': label,
             'armor': armor_ok}, allow_empty=armor_ok)
        if isinstance(act, PlayCards) and not act.cids and armor_ok:
            flip = eng.judge_flip(target, BAGUA)
            if flip is not None and flip.color == CARD_COLOR['red']:
                eng.emit('dodge', nick=target.nick, label=target.armor.label)
                return True
            armor_ok = False   # 判定失败，本次响应不能再判
            continue
        if isinstance(act, PlayCards):
            shan = eng.play_card(target, act.cids[0])
            eng.emit('dodge', nick=target.nick, label=shan.label)
            return True
        return False   # Pass


class TrickRule:
    """锦囊基类：结算前先开无懈可击窗口；子类实现 effect()。

    negate_whole：True = 整牌一个窗口（单目标锦囊）；
    False = 不设整牌窗口，由 effect() 自行对每个目标开窗（AOE/桃园/五谷）。
    延时锦囊使用时仅置入判定区，不开窗口——无懈可击的时机是判定阶段、
    翻判定牌之前（见 judge()）。

    response_name：目标响应此锦囊所需的牌名（决斗→杀），在无懈可击窗口中
    提示给目标本人；None 表示无响应牌（顺手/过河等）。
    """

    type = TRICK
    delayed = False
    negate_whole = True
    response_name = None

    def resolve(self, eng, source, card, action) -> Frame:
        target_nick = action.target or source.nick
        eng.emit('card_used', nick=source.nick, label=card.label,
                 target=action.target)
        if self.delayed:
            used = eng.take_card(source, card.cid)
        else:
            used = eng.play_card(source, card.cid)
            if self.negate_whole:
                negated = yield from eng.negation_window(
                    source, card.label, target_nick,
                    response=self.response_name)
                if negated:
                    eng.emit('negated', label=card.label, target=target_nick)
                    return
        frame = self.effect(eng, source, used, action)
        if frame is not None:
            yield from frame

    def effect(self, eng, source, card, action) -> Frame | None:
        raise NotImplementedError


class EquipRule:
    """装备基类：置入对应槽位，被替换的旧装备置入弃牌堆。

    出牌阶段额外选项（虚拟牌等，如丈八蛇矛两牌当杀，见
    equip/weapon.py 的 ZhangbaRule）：子类设定 extra_key 并实现
    play_extra / check_extra / resolve_extra；引擎在出牌询问中将
    各选项以 extra_key 平铺进 Ask data。
    """

    type = EQUIP
    slot = None
    extra_key: str | None = None   # 额外选项在出牌 Ask data 中的键

    def __init__(self, name: str):
        self.name = name

    def play_targets(self, eng, p, card):
        return []

    def play_extra(self, eng, p):
        """出牌阶段额外选项的可选目标列表；无额外选项或当前不可用返回 None。"""
        return None

    def check_extra(self, p, action, targets) -> bool:
        """action 是否命中本规则的额外选项。"""
        raise NotImplementedError

    def resolve_extra(self, eng, p, action) -> Frame:
        """额外选项的结算帧。"""
        raise NotImplementedError

    def resolve(self, eng, source, card, action):
        used = eng.take_card(source, card.cid)
        old = getattr(source, self.slot)
        if old is not None:
            eng.to_discard(old)
            eng.emit('unequip', nick=source.nick, label=old.label)
        setattr(source, self.slot, used)
        eng.emit('equip', nick=source.nick, label=used.label)
