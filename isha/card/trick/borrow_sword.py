"""借刀杀人：指定一名装备武器的角色对你选择的另一角色出杀，否则你获得其武器。

借出的杀不占出牌次数（复用 ShaRule.sha_effect）。
"""

from isha.core.actions import PlayCards
from isha.core.asks import Ask
from isha.core.engine import Frame
from isha.dict.card import CARD_NAME

from ..base import SHA, TrickRule


class BorrowSwordRule(TrickRule):
    name = CARD_NAME['borrow']

    def play_targets(self, eng, p, card):
        targets = [q.nick for q in eng.alive() if q is not p and q.weapon
                   and self._victims(eng, q)]
        return targets or None

    def _victims(self, eng, holder):
        return [q.nick for q in eng.alive() if q is not holder
                and eng.distance(holder.nick, q.nick) <= holder.range]

    def effect(self, eng, source, card, action) -> Frame:
        holder = eng.player(action.target)
        victims = self._victims(eng, holder)

        def check(act):
            if not isinstance(act, PlayCards) or act.cids:
                return '只能指定目标玩家，不需要选牌'
            if act.target not in victims:
                return '请选择其攻击范围内的一名角色'
            return True

        act = yield Ask(source.nick, 'choose_player',
                        {'holder': holder.nick, 'targets': victims},
                        check, default=PlayCards(source.nick, (), victims[0]))
        victim = eng.player(act.target)
        eng.emit('borrow', nick=source.nick, holder=holder.nick,
                 target=victim.nick)
        shas = [c for c in holder.hand if c.name == SHA]
        if shas:
            act2 = yield eng.card_response_ask(
                holder.nick, 'borrow_sha', shas,
                {'source': source.nick, 'target': victim.nick})
            if isinstance(act2, PlayCards):
                used = eng.play_card(holder, act2.cids[0])
                eng.emit('card_used', nick=holder.nick, label=used.label,
                         target=victim.nick)
                yield from eng.rules[eng.sha_card].sha_effect(
                    eng, holder, victim, used.label, used.color)   # 借刀的杀不占出牌次数
                return
        weapon = holder.weapon
        holder.weapon = None
        eng.gain_card(source, weapon)   # 明牌获得：进手时随机插入/洗乱，位置不泄露
        eng.emit('weapon_gained', nick=source.nick, target=holder.nick,
                 label=weapon.label)
