"""玩家状态：手牌、判定区、装备区与基础属性。"""

from __future__ import annotations

from isha.dict.identity import IDENTITY

from .cards import Card


class PlayerState:
    def __init__(self, nick: str, identity: str, seat: int):
        self.nick = nick
        self.identity = identity
        self.seat = seat
        self.alive = True
        self.max_hp = 4
        self.hp = 4
        self.used_sha = False   # 本回合是否已出杀
        self.skip_play = False  # 本回合是否跳过出牌阶段（乐不思蜀）
        self.hand: list[Card] = []
        self.judgement: list[Card] = []   # 判定区（延时锦囊，后到先判）
        # 装备区
        self.weapon: Card | None = None
        self.armor: Card | None = None
        self.plus_horse: Card | None = None    # +1 马：别人算到我的距离 +1
        self.minus_horse: Card | None = None   # -1 马：我算到别人的距离 -1

    @property
    def range(self) -> int:
        """攻击范围：装备武器时为武器规格，否则为 1。"""
        if self.weapon is not None:
            return int(self.weapon.spec or 1)
        return 1

    @property
    def is_king(self) -> bool:
        return self.identity == IDENTITY['king']

    def find(self, cid: int) -> Card | None:
        for card in self.hand:
            if card.cid == cid:
                return card
        return None

    def take(self, cid: int) -> Card | None:
        for i, card in enumerate(self.hand):
            if card.cid == cid:
                return self.hand.pop(i)
        return None

    def equips(self) -> list[Card]:
        return [c for c in (self.weapon, self.armor, self.plus_horse,
                            self.minus_horse) if c is not None]

    def find_equip(self, cid: int) -> tuple[str, Card] | None:
        """按 cid 找装备，返回 (槽位名, 牌)。"""
        for slot in ('weapon', 'armor', 'plus_horse', 'minus_horse'):
            card = getattr(self, slot)
            if card is not None and card.cid == cid:
                return slot, card
        return None

    def public_identity(self) -> str:
        """对他人可见的身份：主公与死者公开，其余未知。"""
        if self.is_king or not self.alive:
            return self.identity
        return IDENTITY['unknown']
