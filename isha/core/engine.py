"""游戏引擎：纯状态机，与 IO 彻底分离。

用法：

    engine = Engine(players, deck, rules, rng)   # players: [(nick, identity)]
    while not engine.winner:
        ask = engine.pending
        action = collect(ask)                    # 前端收集输入，或超时 engine.timeout()
        effects = engine.apply(action)           # 渲染 effects（公开信息，可广播）

结算栈用生成器调用树实现：yield Ask 挂起等待输入，yield from 嵌套子结算
（杀 → 闪响应 → 伤害 → 濒死求桃；将来无懈可击链同理再叠一层）。
"""

from __future__ import annotations

import random
from collections.abc import Generator

from isha.dict.card import CARD_NAME
from isha.dict.identity import IDENTITY

from .actions import Action, DiscardCards, Pass, PlayCards
from .asks import Ask
from .calculator import seat_distance
from .cards import Card
from .effects import Effect
from .player import PlayerState


class IllegalAction(Exception):
    pass


# 结算帧：产出 Ask、接收 Action 的生成器
Frame = Generator[Ask, Action, None]


class Engine:
    def __init__(self, players: list[tuple[str, str]], deck: list[Card],
                 rules: dict, rng: random.Random, rescue_card: str = '桃',
                 negate_card: str = '无懈可击'):
        self.players = [PlayerState(nick, ident, seat)
                        for seat, (nick, ident) in enumerate(players)]
        self.deck = list(deck)
        self.discard_pile: list[Card] = []
        self.rules = rules   # name -> CardRule（play_targets / resolve / judge）
        self.rng = rng
        self.rescue_card = rescue_card
        self.negate_card = negate_card
        self.sha_card = CARD_NAME['sha']
        self.pending: Ask | None = None
        self.winner: str | None = None
        self.current: PlayerState | None = None   # 当前回合玩家
        self.turn_no = 0
        self.phase = ''
        self._effects: list[Effect] = []
        self._inbox: Action | None = None

        # 5 人及以上局主公 +1 上限（当前支持 5/8 人局）
        if len(self.players) >= 5:
            self.king.max_hp += 1
            self.king.hp += 1

        self._root: Frame | None = self._game()
        self._drive()

    # ---------- 对外 API ----------

    @property
    def king(self) -> PlayerState:
        return next(p for p in self.players if p.is_king)

    def player(self, nick: str) -> PlayerState:
        return next(p for p in self.players if p.nick == nick)

    def alive(self) -> list[PlayerState]:
        return [p for p in self.players if p.alive]

    def distance(self, nick_a: str, nick_b: str):
        """a 到 b 的方向距离：座位距离 - a 的 -1 马 + b 的 +1 马，最小为 1。"""
        base = seat_distance([p.nick for p in self.alive()], nick_a, nick_b)
        if base == 'NaN':
            return base
        a, b = self.player(nick_a), self.player(nick_b)
        return max(1, base - (1 if a.minus_horse else 0)
                   + (1 if b.plus_horse else 0))

    def seat_order_from(self, target: PlayerState) -> list[PlayerState]:
        """从 target 起按座次的存活玩家列表（含 target 自己）。"""
        n = len(self.players)
        i = self.players.index(target)
        return [p for k in range(n)
                if (p := self.players[(i + k) % n]).alive]

    def next_alive(self, p: PlayerState) -> PlayerState | None:
        """p 的下一位存活玩家；无则 None。"""
        n = len(self.players)
        i = self.players.index(p)
        for k in range(1, n + 1):
            q = self.players[(i + k) % n]
            if q.alive:
                return q
        return None

    def apply(self, action: Action) -> list[Effect]:
        if self.winner:
            raise IllegalAction('游戏已结束')
        ask = self.pending
        if ask is None:
            raise IllegalAction('当前无需操作')
        if action.player != ask.player:
            raise IllegalAction(f'应当由 {ask.player} 行动')
        verdict = ask.check(action)
        if verdict is not True:
            # check 可返回具体原因字符串；返回 False 则给通用提示
            reason = verdict if isinstance(verdict, str) else '不符合当前窗口的操作要求'
            raise IllegalAction(reason)
        self.pending = None
        self._inbox = action
        self._drive()
        return self.drain_effects()

    def timeout(self) -> list[Effect]:
        """注入当前响应窗口的超时默认动作。"""
        if self.pending is None:
            raise IllegalAction('当前无需操作')
        return self.apply(self.pending.default)

    def drain_effects(self) -> list[Effect]:
        effects, self._effects = self._effects, []
        return effects

    def emit(self, kind: str, **data):
        """记录一条公开事件；规则层的结算帧同样通过它产出 Effect。"""
        self._effects.append(Effect(kind, **data))

    # ---------- 牌堆 ----------

    def draw_one(self) -> Card | None:
        """从牌堆顶取一张牌（牌堆空则洗回弃牌堆）；无牌可取返回 None。"""
        if not self.deck:
            if not self.discard_pile:
                return None
            self.deck, self.discard_pile = self.discard_pile, []
            self.rng.shuffle(self.deck)
            self.emit('reshuffle')
        return self.deck.pop(0)

    def draw(self, p: PlayerState, n: int):
        got = 0
        for _ in range(n):
            card = self.draw_one()
            if card is None:
                break
            p.hand.append(card)
            got += 1
        self.emit('draw', nick=p.nick, count=got)

    def gain_card(self, p: PlayerState, card: Card):
        """一张已公开的牌进入手牌（五谷挑选、顺手、借刀得武器等）。

        当前回合玩家插入随机位置；非本回合玩家则追加后整手洗乱——
        否则旁观者能凭位置记忆推算新牌（如"末尾就是五谷拿的那张"），
        暗牌盲选（顺手/过河）就失去了意义。
        """
        if p is self.current:
            p.hand.insert(self.rng.randrange(len(p.hand) + 1), card)
        else:
            p.hand.append(card)
            self.rng.shuffle(p.hand)

    def judge_flip(self, p: PlayerState, reason: str) -> Card | None:
        """翻牌判定：展示牌堆顶一张牌并弃置。"""
        card = self.draw_one()
        self.emit('judge_flip', nick=p.nick, reason=reason,
                  label=card.label if card else '?')
        if card:
            self.to_discard(card)
        return card

    def to_discard(self, card: Card):
        self.discard_pile.append(card)

    def take_card(self, p: PlayerState, cid: int) -> Card:
        """从手牌取出（不进入弃牌堆，供置入判定区等场景）。"""
        return p.take(cid)

    def play_card(self, p: PlayerState, cid: int) -> Card:
        """从手牌取出并置入弃牌堆（桌面概念从简，直接进入弃牌堆）。"""
        card = p.take(cid)
        self.to_discard(card)
        return card

    # ---------- 响应窗口 ----------

    def card_response_ask(self, player: str, kind: str, cards: list[Card],
                          data: dict, allow_empty: bool = False) -> Ask:
        """通用"从手牌打出一张指定牌或放弃"的询问。

        data['cards'] 统一为 (cid, label) 列表，供前端渲染可打出的牌。
        allow_empty=True 时允许空 cids 的 PlayCards（八卦阵判定等特效）。
        """
        allowed = [c.cid for c in cards]

        def check(act):
            if isinstance(act, Pass):
                return True
            if not isinstance(act, PlayCards):
                return '只能打出牌或放弃'
            if not act.cids:
                if allow_empty:
                    return True
                return '当前不能空出牌'
            if len(act.cids) != 1:
                return '一次只能打出一张牌'
            if act.cids[0] not in allowed:
                labels = '、'.join(f'【{c.label}】' for c in cards)
                return f'只能打出这些牌：{labels}' if labels else '当前无牌可打'
            return True

        return Ask(player, kind,
                   {**data, 'cards': [(c.cid, c.label) for c in cards]},
                   check, default=Pass(player))

    def negation_window(self, source: PlayerState, trick_label: str,
                        target_nick: str, skip: set | None = None,
                        response: str | None = None) -> Frame:
        """无懈可击窗口：从 source 起按座次询问所有存活玩家。

        有人出无懈可击则重新开一轮询问（抵消可以嵌套抵消）；
        完整一圈无人响应后结算：奇数次抵消 → 锦囊被抵消。

        skip：同一张锦囊逐目标开窗时传入同一集合，玩家以 Pass(rest=True)
        表示本张锦囊后续窗口不再询问；一旦有人打出无懈可击则清空 skip
        ——新一轮询问中所有人（包括之前 rest 的玩家）重新获得机会。

        response：目标响应此锦囊所需的牌名（南蛮/决斗→杀，万箭→闪）。
        被询问者即目标本人时，Ask data 附带 response_name 与其手上的
        response_cards，便于玩家结合自己的响应牌决定是否动用无懈可击；
        第三方被询问时不附带（目标手牌对其保密）。
        """
        depth = 0
        while True:
            played = False
            for p in self.seat_order_from(source):
                if skip is not None and p.nick in skip:
                    continue
                cards = [c for c in p.hand if c.name == self.negate_card]
                if not cards:
                    continue
                data = {'trick': trick_label, 'target': target_nick}
                if response is not None and p.nick == target_nick:
                    data['response_name'] = response
                    data['response_cards'] = [(c.cid, c.label) for c in p.hand
                                              if c.name == response]
                act = yield self.card_response_ask(p.nick, 'negate', cards,
                                                   data)
                if isinstance(act, PlayCards):
                    used = self.play_card(p, act.cids[0])
                    self.emit('negate_used', nick=p.nick, label=used.label,
                              trick=trick_label)
                    depth += 1
                    played = True
                    if skip is not None:
                        skip.clear()
                    break
                if skip is not None and isinstance(act, Pass) and act.rest:
                    skip.add(p.nick)
            if not played:
                return depth % 2 == 1

    # ---------- 结算（供规则与内部使用） ----------

    def damage(self, source: PlayerState | None, target: PlayerState, amount: int) -> Frame:
        target.hp -= amount
        self.emit('damaged', nick=target.nick, amount=amount, hp=target.hp,
                  source=source.nick if source else None)
        if target.hp <= 0:
            yield from self.dying(target, source)

    def dying(self, target: PlayerState, source: PlayerState | None) -> Frame:
        self.emit('dying', nick=target.nick)
        for p in self.seat_order_from(target):
            while target.hp <= 0:
                rescues = [c for c in p.hand if c.name == self.rescue_card]
                if not rescues:
                    break
                act = yield self.card_response_ask(p.nick, 'peach', rescues,
                                                   {'target': target.nick})
                if isinstance(act, Pass):
                    break
                used = self.play_card(p, act.cids[0])
                target.hp += 1
                self.emit('peach_used', nick=p.nick, label=used.label,
                          target=target.nick, hp=target.hp)
            if target.hp > 0:
                break
        if target.hp <= 0:
            self._death(target, source)

    # ---------- 内部 ----------

    def _drive(self):
        while self._root is not None:
            try:
                ask = self._root.send(self._inbox)
            except StopIteration:
                self._root = None
                break
            self._inbox = None
            if ask is not None:
                self.pending = ask
                return
        self.pending = None

    def _game(self) -> Frame:
        self.emit('game_start', seats=[p.nick for p in self.players],
                   king=self.king.nick)
        for p in self.players:
            self.draw(p, 4)
        i = self.players.index(self.king)
        while not self.winner:
            p = self.players[i]
            if p.alive:
                self.current = p
                yield from self._turn(p)
                self.current = None
            i = (i + 1) % len(self.players)

    def _turn(self, p: PlayerState) -> Frame:
        self.turn_no += 1
        p.used_sha = False
        p.skip_play = False
        self.emit('turn_start', nick=p.nick, turn=self.turn_no)
        self.phase = 'judge'
        yield from self._judge_phase(p)
        if self.winner or not p.alive:
            return   # 玩家在判定阶段死亡（如被自己的闪电命中），回合直接中止
        self.phase = 'draw'
        self.draw(p, 2)
        self.phase = 'play'
        while not self.winner and not p.skip_play and p.alive:
            action = yield self._play_ask(p)
            if isinstance(action, Pass):
                break
            extra = next((r for r, t in self._play_extras(p)
                          if r.check_extra(p, action, t)), None)
            if extra is not None:   # 装备提供的额外选项（如丈八蛇矛两牌当杀）
                yield from extra.resolve_extra(self, p, action)
                continue
            card = p.find(action.cids[0])
            frame = self.rules[card.name].resolve(self, p, card, action)
            if frame is not None:   # 规则返回结算帧则驱动；返回 None 表示已同步完成
                yield from frame
        if self.winner or not p.alive:
            return   # 出牌阶段死亡（如决斗失利），不弃牌、回合中止
        self.phase = 'discard'
        excess = len(p.hand) - p.hp
        if excess > 0:
            action = yield self._discard_ask(p, excess)
            for cid in action.cids:
                self.to_discard(p.take(cid))
            self.emit('discard', nick=p.nick, count=excess)
        self.phase = ''
        self.emit('turn_end', nick=p.nick)

    def _judge_phase(self, p: PlayerState) -> Frame:
        """判定阶段：处理判定区的延时锦囊，后到先判（LIFO）。

        玩家在判定中途死亡（如被自己的闪电命中）时，_death 已将其
        判定区清空，循环自然终止。
        """
        while p.judgement and p.alive and not self.winner:
            card = p.judgement.pop()
            rule = self.rules.get(card.name)
            frame = rule.judge(self, p, card) if rule and hasattr(rule, 'judge') else None
            if frame is not None:
                yield from frame
            elif not rule or not hasattr(rule, 'judge'):
                self.to_discard(card)   # 无判定逻辑的牌直接弃置（防御性分支）

    def _play_ask(self, p: PlayerState) -> Ask:
        options = {}   # cid -> [可指定的目标 nick]；空列表表示无需目标
        multi = {}     # cid -> 可多选的目标上限（方天画戟）
        for card in p.hand:
            targets = self.rules[card.name].play_targets(self, p, card)
            if targets is not None:
                options[card.cid] = targets
                max_targets = getattr(self.rules[card.name], 'max_targets', None)
                if max_targets is not None and targets:
                    limit = max_targets(self, p, card)
                    if limit > 1:
                        multi[card.cid] = limit
        extras = self._play_extras(p)   # 装备提供的额外选项（如丈八蛇矛）
        data = {
            'hand': [(c.cid, c.label) for c in p.hand],
            'options': {cid: tgts for cid, tgts in options.items()},
            'multi': multi,   # 这些牌的 target 可传 nick 列表（长度不超过上限）
            # 额外选项以各自的 extra_key 平铺（如 'zhangba': 目标列表）
            **{r.extra_key: t for r, t in extras},
        }

        def check(action):
            if isinstance(action, Pass):
                return True
            if not isinstance(action, PlayCards):
                return '出牌阶段只能使用牌或结束出牌'
            if any(r.check_extra(p, action, t) for r, t in extras):
                return True
            if len(action.cids) != 1:
                return '一次只能使用一张牌'
            cid = action.cids[0]
            card = p.find(cid)
            if card is None:
                return '你手里没有这张牌'
            if cid not in options:
                if card.name == self.sha_card and p.used_sha:
                    return '本回合已经出过杀了（诸葛连弩可不受限）'
                return f'【{card.label}】当前不满足使用条件'
            targets = options[cid]
            if not targets:
                if action.target is not None:
                    return '该牌不能指定目标'
                return True
            if isinstance(action.target, (list, tuple)):
                # 多目标（方天画戟）：全部合法、不重复、不超过上限
                limit = multi.get(cid, 1)
                if limit <= 1:
                    return '该牌只能指定一名目标'
                chosen = list(action.target)
                if not 1 <= len(chosen) <= limit:
                    return f'该牌至多指定 {limit} 名目标'
                if len(set(chosen)) != len(chosen):
                    return '不能重复指定同一目标'
                if not all(t in targets for t in chosen):
                    return '含有不合法或超出范围的目标'
                return True
            if action.target not in targets:
                return '目标不合法或超出范围'
            return True

        return Ask(p.nick, 'play', data, check, default=Pass(p.nick))

    def _play_extras(self, p: PlayerState) -> list:
        """装备规则提供的出牌阶段额外选项：[(rule, 目标列表)]（如丈八蛇矛）。"""
        extras = []
        for equip in p.equips():
            rule = self.rules.get(equip.name)
            play_extra = getattr(rule, 'play_extra', None)
            if play_extra is None:
                continue
            targets = play_extra(self, p)
            if targets is not None:
                extras.append((rule, targets))
        return extras

    def _discard_ask(self, p: PlayerState, excess: int) -> Ask:
        data = {'count': excess, 'hand': [(c.cid, c.label) for c in p.hand]}

        def check(action):
            if not isinstance(action, DiscardCards):
                return '弃牌阶段只能弃牌'
            if len(action.cids) != excess:
                return f'需要恰好弃置 {excess} 张牌'
            if len(set(action.cids)) != excess:
                return '不能重复选择同一张牌'
            if not all(p.find(cid) is not None for cid in action.cids):
                return '只能弃置自己的手牌'
            return True

        default = DiscardCards(p.nick, tuple(c.cid for c in p.hand[:excess]))
        return Ask(p.nick, 'discard', data, check, default=default)

    def _death(self, victim: PlayerState, killer: PlayerState | None):
        victim.alive = False
        # 死亡时所有牌（手牌、判定区、装备区）全部置入弃牌堆
        for card in victim.hand:
            self.to_discard(card)
        victim.hand = []
        for card in victim.judgement:
            self.to_discard(card)
        victim.judgement = []
        for card in victim.equips():
            self.to_discard(card)
        victim.weapon = victim.armor = None
        victim.plus_horse = victim.minus_horse = None
        self.emit('died', nick=victim.nick, identity=victim.identity)

        if killer is not None and killer.alive:
            if victim.identity == IDENTITY['rebel']:
                self.emit('reward', nick=killer.nick, count=3)
                self.draw(killer, 3)
            if killer.is_king and victim.identity == IDENTITY['minister']:
                # 主公误杀忠臣：弃置其所有牌（手牌 + 装备区；判定区牌不属于角色，不动）
                cards = killer.hand + killer.equips()
                for card in cards:
                    self.to_discard(card)
                killer.hand = []
                killer.weapon = killer.armor = None
                killer.plus_horse = killer.minus_horse = None
                self.emit('punish', nick=killer.nick, count=len(cards))

        self._check_win()

    def _check_win(self):
        alive = self.alive()
        if not self.king.alive:
            # 内奸唯一存活且主公阵亡 → 内奸胜；否则反贼胜
            if len(alive) == 1 and alive[0].identity == IDENTITY['traitor']:
                self._game_over(IDENTITY['traitor'])
            else:
                self._game_over(IDENTITY['rebel'])
        elif not any(p.identity in (IDENTITY['rebel'], IDENTITY['traitor'])
                     for p in alive):
            self._game_over(f"{IDENTITY['king']}阵营")

    def _game_over(self, winner: str):
        self.winner = winner
        self.emit('game_over', winner=winner)
