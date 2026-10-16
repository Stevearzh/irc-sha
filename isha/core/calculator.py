"""座位距离：只在存活玩家构成的环上计算（死亡玩家离场，距离随之收缩）。"""


def cyclic_distance(a: int, b: int, n: int) -> int:
    d = abs(a - b)
    return min(d, n - d)


def seat_distance(alive_nicks: list[str], nick_a: str, nick_b: str) -> int | str:
    """alive_nicks 按座次排列；任一玩家不在场（死亡/不存在）返回 'NaN'。"""
    try:
        pos_a = alive_nicks.index(nick_a)
        pos_b = alive_nicks.index(nick_b)
    except ValueError:
        return 'NaN'
    return cyclic_distance(pos_a, pos_b, len(alive_nicks))
