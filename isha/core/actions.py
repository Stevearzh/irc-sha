"""玩家动作：前端（CLI/IRC/测试）把玩家输入解析为 Action 喂给引擎。"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PlayCards:
    """出牌/响应：cids 为手牌 cid；target 为目标 nick（自摸类牌为 None）。"""

    player: str
    cids: tuple[int, ...]
    target: str | None = None


@dataclass(frozen=True)
class DiscardCards:
    """弃牌：弃牌阶段弃掉指定 cids。"""

    player: str
    cids: tuple[int, ...]


@dataclass(frozen=True)
class Pass:
    """放弃响应/结束出牌阶段。

    rest=True 仅在无懈可击窗口有意义：本张锦囊的后续响应窗口都不再询问；
    一旦有人打出无懈可击开启新一轮询问，该偏好作废（见 negation_window）。
    """

    player: str
    rest: bool = False


Action = PlayCards | DiscardCards | Pass
