"""引擎对外输出的事件。

约定：Effect 只含公开信息，可直接广播到 IRC 频道；
私密信息（手牌、可选动作）仅通过 Ask.data 发给对应玩家。
"""

from dataclasses import dataclass, field


@dataclass
class Effect:
    kind: str
    data: dict = field(default_factory=dict)

    def __init__(self, kind: str, **data):
        self.kind = kind
        self.data = data
