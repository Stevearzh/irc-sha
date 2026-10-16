"""闪：响应杀/万箭齐发时打出以抵消，不能主动使用。"""

from ..base import BASIC, SHAN


class ShanRule:
    name = SHAN
    type = BASIC

    def play_targets(self, eng, p, card) -> None:
        return None   # 闪只能在响应杀/万箭时被动使用

    def resolve(self, eng, source, card, action):
        raise NotImplementedError('闪不能主动使用')
