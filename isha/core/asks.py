"""响应窗口：引擎需要玩家输入时挂起并暴露 pending: Ask。

- player：应当行动的玩家 nick
- kind：窗口类型（play / respond_sha / peach / discard）
- data：给前端的渲染上下文（含私密选项，只发给该玩家）
- check：动作合法性校验，apply() 据此拒绝非法输入；返回 True 表示合法，
  返回字符串表示非法且该串为具体原因（返回 False 则给出通用提示）
- default：超时默认动作，前端调 engine.timeout() 时注入
"""

from dataclasses import dataclass, field
from typing import Callable

from .actions import Action


@dataclass
class Ask:
    player: str
    kind: str
    data: dict = field(default_factory=dict)
    check: Callable[[Action], bool] = lambda action: False
    default: Action = None
