"""无懈可击：在锦囊生效前的响应窗口中打出，抵消该锦囊对一名目标的效果。

不能主动使用；响应窗口与嵌套抵消逻辑见 engine.negation_window。
"""

from ..base import NEGATE, TRICK


class NegateRule:
    name = NEGATE
    type = TRICK

    def play_targets(self, eng, p, card) -> None:
        return None   # 只能在锦囊生效前的响应窗口中使用

    def resolve(self, eng, source, card, action):
        raise NotImplementedError('无懈可击不能主动使用')
