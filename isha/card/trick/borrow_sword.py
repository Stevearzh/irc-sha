"""借刀杀人：指定一名装备武器的角色对你选择的另一角色出杀，否则你获得其武器。

借出的杀不占出牌次数（复用 ShaRule.sha_effect）。
目标装备丈八蛇矛且手牌不少于两张时，也可用两张手牌当杀（虚拟杀）。
"""

from isha.core.actions import Pass, PlayCards
from isha.core.asks import Ask
from isha.core.engine import Frame
from isha.dict.card import CARD_NAME

from ..base import SHA, TrickRule

ZHANGBA = CARD_NAME['zhangba']


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
        # 丈八蛇矛：手牌不少于两张时可任选两张当杀
        zhangba = holder.weapon is not None \
            and holder.weapon.name == ZHANGBA and len(holder.hand) >= 2
        if shas or zhangba:
            act2 = yield self._sha_ask(eng, holder, source, victim,
                                       shas, zhangba)
            if isinstance(act2, PlayCards):
                if len(act2.cids) == 2:   # 丈八蛇矛：两张手牌当杀
                    yield from eng.rules[ZHANGBA].as_sha(
                        eng, holder, act2.cids, victim.nick)
                else:
                    used = eng.play_card(holder, act2.cids[0])
                    eng.emit('card_used', nick=holder.nick, label=used.label,
                             target=victim.nick)
                    yield from eng.rules[eng.sha_card].sha_effect(
                        eng, holder, victim, used.label, used.color)
                return
        weapon = holder.weapon
        holder.weapon = None
        eng.gain_card(source, weapon)   # 明牌获得：进手时随机插入/洗乱，位置不泄露
        eng.emit('weapon_gained', nick=source.nick, target=holder.nick,
                 label=weapon.label)

    def _sha_ask(self, eng, holder, source, victim, shas, zhangba) -> Ask:
        """出杀响应窗口：打出一张杀；有丈八蛇矛时也可打出两张手牌当杀。"""
        sha_cids = {c.cid for c in shas}

        def check(act):
            if isinstance(act, Pass):
                return True
            if not isinstance(act, PlayCards):
                return '只能打出杀或放弃'
            if len(act.cids) == 1:
                if act.cids[0] in sha_cids:
                    return True
                return '只能打出杀（丈八蛇矛可打出两张手牌当杀）' if zhangba \
                    else '只能打出杀'
            if len(act.cids) == 2 and zhangba:
                c1, c2 = act.cids
                if c1 != c2 and holder.find(c1) and holder.find(c2):
                    return True
                return '丈八蛇矛需要打出两张不同的手牌'
            return '一次只能打出一张杀' + ('或两张手牌当杀' if zhangba else '')

        return Ask(holder.nick, 'borrow_sha',
                   {'source': source.nick, 'target': victim.nick,
                    'cards': [(c.cid, c.label) for c in shas],
                    'zhangba': zhangba},
                   check, default=Pass(holder.nick))
