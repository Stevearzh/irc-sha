"""杀：出牌阶段对攻击范围内一名角色使用，其需打出闪否则受到 1 点伤害。

武器特效集中于此：诸葛连弩（不限次数）、贯石斧（被闪避后弃二强命）、
青龙偃月刀（追杀）、麒麟弓（命中后射马）、寒冰剑（防止伤害改弃两张牌）、
方天画戟（杀为最后一张手牌时可多指定至多两名目标，逐目标按座次结算）、
青釭剑（无视防具，见 base.dodge_window 与仁王盾判定）；丈八蛇矛
（两张手牌当杀）见 card/equip/weapon.py 的 ZhangbaRule。
sha_effect 被丈八蛇矛虚拟杀、借刀杀人、青龙追杀复用。
仁王盾（黑色的杀无效）也在 sha_effect 开头判定。
"""

from isha.core.actions import DiscardCards, Pass, PlayCards
from isha.core.asks import Ask
from isha.core.engine import Frame
from isha.dict.card import CARD_COLOR

from ..base import (BASIC, FANGTIAN, GUANSHI, ICESWORD, QINGLONG, QILIN,
                    RENWANG, SHA, ZHUGE, dodge_window, ignores_armor)


class ShaRule:
    name = SHA
    type = BASIC

    def play_targets(self, eng, p, card) -> list[str] | None:
        if p.used_sha and not (p.weapon and p.weapon.name == ZHUGE):
            return None   # 诸葛连弩不受一回合一张限制
        return [q.nick for q in eng.alive()
                if q is not p and eng.distance(p.nick, q.nick) <= p.range]

    def max_targets(self, eng, p, card) -> int:
        """方天画戟：使用的杀是最后一张手牌时，可额外多指定至多两名目标。"""
        if p.weapon is not None and p.weapon.name == FANGTIAN \
                and len(p.hand) == 1:
            return 3
        return 1

    def resolve(self, eng, source, card, action) -> Frame:
        source.used_sha = True
        chosen = action.target
        if not isinstance(chosen, (list, tuple)):
            chosen = (chosen,)
        eng.play_card(source, card.cid)
        eng.emit('card_used', nick=source.nick, label=card.label,
                 target='、'.join(chosen))
        # 多目标（方天画戟）：从来源起按座次逐名结算
        victims = [q for q in eng.seat_order_from(source) if q.nick in chosen]
        for victim in victims:
            if eng.winner:
                break
            if not victim.alive:
                continue
            yield from self.sha_effect(eng, source, victim, card.label,
                                       card.color)

    def sha_effect(self, eng, source, target, label: str,
                   color: str = CARD_COLOR['no_color']) -> Frame:
        """杀生效流程（丈八蛇矛虚拟杀、借刀杀人、追杀均复用）。

        color 为杀的颜色（丈八蛇矛虚拟杀：两牌同色取该色，异色为无色）。
        武器特效：贯石斧（被闪避后弃二强命）、青龙偃月刀（追杀）、
        麒麟弓（命中后射马）、寒冰剑（命中时防止伤害改弃两张牌）、
        青釭剑（无视防具）；仁王盾使黑色的杀直接无效。
        """
        if target.armor is not None and target.armor.name == RENWANG \
                and color == CARD_COLOR['black'] and not ignores_armor(source):
            eng.emit('renwang', nick=target.nick, label=label)
            return
        dodged = yield from dodge_window(eng, source, target, label)
        weapon = source.weapon.name if source.weapon else None
        if dodged:
            if weapon == GUANSHI and len(source.hand) >= 2:
                act = yield self._guanshi_ask(eng, source, target)
                if isinstance(act, DiscardCards):
                    for cid in act.cids:
                        eng.to_discard(source.take(cid))
                    eng.emit('guanshi', nick=source.nick, target=target.nick)
                    yield from eng.damage(source, target, 1)
            elif weapon == QINGLONG:
                shas = [c for c in source.hand if c.name == SHA]
                if shas:
                    act = yield eng.card_response_ask(
                        source.nick, 'chase', shas, {'target': target.nick})
                    if isinstance(act, PlayCards):
                        used = eng.play_card(source, act.cids[0])
                        eng.emit('card_used', nick=source.nick,
                                 label=used.label, target=target.nick)
                        yield from self.sha_effect(eng, source, target,
                                                   used.label, used.color)
            return
        if weapon == ICESWORD and (target.hand or target.equips()):
            prevented = yield from self._icesword(eng, source, target)
            if prevented:
                return
        yield from eng.damage(source, target, 1)
        if weapon == QILIN and target.alive:
            horses = [c for c in (target.plus_horse, target.minus_horse) if c]
            if horses:
                act = yield eng.card_response_ask(
                    source.nick, 'qilin', horses, {'target': target.nick})
                if isinstance(act, PlayCards):
                    slot, horse = target.find_equip(act.cids[0])
                    setattr(target, slot, None)
                    eng.to_discard(horse)
                    eng.emit('horse_shot', nick=source.nick,
                             target=target.nick, label=horse.label)

    def _guanshi_ask(self, eng, source, target) -> Ask:
        def check(act):
            if isinstance(act, Pass):
                return True
            if not isinstance(act, DiscardCards):
                return '贯石斧需要弃置手牌，或放弃'
            if len(act.cids) != 2 or len(set(act.cids)) != 2:
                return '贯石斧需要弃置恰好两张不同的手牌'
            if not all(source.find(cid) for cid in act.cids):
                return '只能弃置自己的手牌'
            return True

        return Ask(source.nick, 'guanshi',
                   {'target': target.nick, 'count': 2,
                    'hand': [(c.cid, c.label) for c in source.hand]},
                   check, default=Pass(source.nick))

    def _icesword(self, eng, source, target) -> Frame:
        """寒冰剑：防止伤害，改为依次弃置目标的两张牌。

        可选范围限手牌（暗选盲抽）与装备区（明选），不含判定区；
        目标只有一张牌时弃一张。返回是否防止了伤害。
        """
        discarded = []
        for i in range(2):
            options = ([(c.cid, None) for c in target.hand]
                       + [(c.cid, c.label) for c in target.equips()])
            if not options:
                break
            allowed = [cid for cid, _ in options]
            optional = i == 0   # 第一张可放弃（正常造成伤害），之后必须弃完

            def check(act):
                if optional and isinstance(act, Pass):
                    return True
                if not isinstance(act, PlayCards) or len(act.cids) != 1:
                    return '请选择要弃置的一张牌'
                if act.cids[0] not in allowed:
                    return '只能弃置目标的手牌或装备区中的一张牌'
                return True

            default = Pass(source.nick) if optional \
                else PlayCards(source.nick, (options[0][0],))
            act = yield Ask(source.nick, 'icesword',
                            {'target': target.nick, 'cards': options,
                             'optional': optional},
                            check, default=default)
            if isinstance(act, Pass):
                return False
            cid = act.cids[0]
            card = target.find(cid)
            if card is not None:
                target.hand.remove(card)
            else:
                slot, card = target.find_equip(cid)
                setattr(target, slot, None)
            eng.to_discard(card)
            discarded.append(card)
        if not discarded:
            return False
        eng.emit('icesword', nick=source.nick, target=target.nick,
                 labels=[c.label for c in discarded])
        return True
