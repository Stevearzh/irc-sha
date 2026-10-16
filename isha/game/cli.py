"""本地热座 CLI：所有玩家在同一终端轮流操作，用于验证 Ask/Action 交互。

用法：
    python -m isha.game.cli [--ex] [nick1 nick2 ...]
                            # 5 或 8 人，缺省 a b c d e
                            # --ex 在标准包之外加入 EX 卡包（4 张）

操作：
    play 阶段       0（手牌序号）或 h10杀（花色+点数+名字，名字可省）；
                    目标可同行给出（0 b / h10杀 b），省略时列出可选目标
                    供二次选择（q / 99 取消）；方天画戟最后一张杀可多目标
                    （s7杀 b c d）；p 结束出牌
    respond_sha     h2闪 / p（不出闪）
    peach           h3桃 / p（不出，本轮濒死不再询问）
    negate          只列出可出的无懈可击；目标本人另提示手上的杀/闪等响应牌；
                    序号/引用出牌；q 本次不出，p 本张锦囊后续窗口都不再询问
    harvest         亮出牌按序号（0 起）或引用选择
    discard         0 1 ... 或 h10杀 s7杀 ...（空格分开，数量须符合要求）
    choose_card     输入序号选择（顺手/过河：暗牌按位置盲选）
    choose_player   输入序号或昵称选择目标玩家（借刀杀人）
    通用            show（看局势）/ hand（看自己手牌）/ help / t（超时托管）
"""

import sys

from isha.core.actions import DiscardCards, Pass, PlayCards
from isha.core.asks import Ask
from isha.core.cards import explain_card_assign, find_card, parse_ref
from isha.core.engine import Engine, IllegalAction

from . import new_game
from .render import render_effect, render_hint, render_table


def show(effects):
    for e in effects:
        line = render_effect(e)
        if line:
            print(line)


def parse_cards(refs: list[str], hand) -> list | None:
    """refs 元素可以是文本引用（h10杀）或手牌序号（0 起，对应展示的手牌列表）。"""
    cards = []
    pool = list(hand)
    for ref in refs:
        if ref.isdigit() and int(ref) < len(hand):
            card = hand[int(ref)]
        else:
            card = find_card(ref, pool)
        if card is None or card not in pool:
            return None
        pool.remove(card)
        cards.append(card)
    return cards


def ask_target(targets: list[str]):
    """二级目标选择：输入序号或昵称；q / 99 取消（返回 None）。"""
    print('   请选择目标：'
          + ' '.join(f'{i}. {t}' for i, t in enumerate(targets))
          + ' 99. q（取消）')
    while True:
        try:
            line = input('> ').strip()
        except EOFError:
            raise KeyboardInterrupt
        if line in ('q', '99'):
            return None
        if line in targets:
            return line
        if line.isdigit() and int(line) < len(targets):
            return targets[int(line)]
        print('   无效目标；输入序号或昵称，q / 99 取消')


def prompt(eng: Engine, ask: Ask):
    p = eng.player(ask.player)
    print(f"\n>> {ask.player}（你是：{p.identity}）行动：{render_hint(ask)}")
    if ask.kind == 'harvest':
        print('   亮出牌：' + ' '.join(f'{i}.{label}'
                     for i, (_, label) in enumerate(ask.data['revealed'])))
    elif ask.kind == 'choose_card':
        print('   可选：' + ' '.join(f'{i}.{label or "暗牌"}'
                                   for i, (_, label) in enumerate(ask.data['cards'])))
    elif 'cards' in ask.data:   # 响应窗口：只列出此刻真正可出的牌
        line_out = '   可出的牌：' + ' '.join(
            f'{i}.{label}' for i, (_, label) in enumerate(ask.data['cards']))
        if ask.kind == 'negate':
            line_out += '（序号/引用出牌；q 本次不出；p 本张锦囊都不再出）'
            if 'response_name' in ask.data:   # 目标本人：列出其响应牌明细
                labels = '、'.join(lab for _, lab in ask.data['response_cards'])
                line_out += (f"；你的【{ask.data['response_name']}】："
                             f"{labels or '（无）'}")
        if ask.kind == 'peach':
            line_out += '（序号/引用出桃；p 不出，本轮濒死不再询问）'
        if ask.data.get('armor'):
            line_out += '（g 八卦阵判定）'
        print(line_out)
    elif ask.kind == 'choose_player':
        print('   可选目标：' + ' '.join(f'{i}. {t}'
              for i, t in enumerate(ask.data['targets'])))
    else:
        # 出牌阶段：标注当前不可使用的牌（如已出过杀、桃满血不可用等）
        parts = []
        for i, c in enumerate(p.hand):
            item = f'{i}.{c.label}'
            if ask.kind == 'play' and c.cid not in ask.data.get('options', {}):
                item += '（不可出）'
            parts.append(item)
        line_out = '   手牌：' + ' '.join(parts)
        if ask.kind == 'play':
            if ask.data.get('multi'):
                line_out += '（方天画戟生效：杀可多选目标，如 s7杀 b c d）'
            line_out += '  p. 结束出牌阶段'
        print(line_out)

    while True:
        try:
            line = input('> ').strip()
        except EOFError:
            raise KeyboardInterrupt
        if not line:
            continue
        if line == 'show':
            print(render_table(eng))
            continue
        if line == 'hand':
            print('手牌：' + ' '.join(f'{i}.{c.label}'
                                    for i, c in enumerate(p.hand)))
            continue
        if line == 'help':
            print(explain_card_assign())
            continue
        if line == 't':
            return None   # 超时托管
        if line == 'g' and ask.data.get('armor'):
            return PlayCards(ask.player, ())   # 八卦阵判定
        if line in ('p', '过', 'pass'):
            if ask.kind == 'discard':
                return None   # 弃牌阶段的 p = 自动弃牌
            if ask.kind == 'negate':
                return Pass(ask.player, rest=True)   # 本张锦囊后续窗口不再询问
            return Pass(ask.player)
        if line in ('q', '99') and ask.kind == 'negate':
            return Pass(ask.player)   # 仅本次不出无懈可击
        if ask.kind in ('discard', 'guanshi'):
            cards = parse_cards(line.split(), p.hand)
            if cards:
                return DiscardCards(ask.player, tuple(c.cid for c in cards))
        elif ask.kind == 'choose_player':
            token = line.split()[0]
            if token.isdigit() and int(token) < len(ask.data['targets']):
                token = ask.data['targets'][int(token)]
            if token in ask.data['targets']:
                return PlayCards(ask.player, (), token)
        elif ask.kind == 'choose_card':
            if line.isdigit() and int(line) < len(ask.data['cards']):
                return PlayCards(ask.player, (ask.data['cards'][int(line)][0],))
        elif ask.kind == 'harvest':
            token = line.split()[0]
            if token.isdigit() and int(token) < len(ask.data['revealed']):
                return PlayCards(ask.player,
                                 (ask.data['revealed'][int(token)][0],))
            ref = parse_ref(token)
            if ref:
                label = ''.join(ref)
                hit = [cid for cid, lab in ask.data['revealed']
                       if lab == label or (not ref[2] and lab.startswith(label))]
                if hit:
                    return PlayCards(ask.player, (hit[0],))
        elif ask.kind == 'play' and ask.data.get('zhangba') \
                and len(line.split()) in (2, 3):
            # 丈八蛇矛：两张牌当杀（"h10杀 s7杀 b" 或序号 "0 2 b"，目标可后补）
            parts = line.split()
            cards = parse_cards(parts[:2], p.hand)
            if cards:
                target = parts[2] if len(parts) == 3 else None
                if target not in ask.data['zhangba']:
                    target = ask_target(ask.data['zhangba'])
                    if target is None:
                        continue
                return PlayCards(ask.player, tuple(c.cid for c in cards),
                                 target)
        else:
            parts = line.split()
            token = parts[0]
            if 'cards' in ask.data and token.isdigit() \
                    and int(token) < len(ask.data['cards']):
                # 响应窗口：序号对应上方"可出的牌"列表
                return PlayCards(ask.player,
                                 (ask.data['cards'][int(token)][0],))
            cards = parse_cards([token], p.hand)
            if cards:
                card = cards[0]
                target = parts[1] if len(parts) > 1 else None
                if ask.kind == 'play':
                    # 需要目标但未给出（或目标无效）：列出可选目标二次选择
                    targets = ask.data['options'].get(card.cid)
                    if targets:
                        limit = ask.data.get('multi', {}).get(card.cid, 1)
                        # 方天画戟等多目标：同行可给多个目标（s7杀 b c d）
                        picks = [t for t in parts[1:] if t in targets][:limit]
                        if not picks:
                            picked = ask_target(targets)
                            if picked is None:
                                continue
                            picks = [picked]
                        target = picks if limit > 1 else picks[0]
                return PlayCards(ask.player, (card.cid,), target)
        print('无法解析输入；输入 help 查看选牌协议，p 跳过，show 看局势')


def main():
    args = sys.argv[1:]
    packs = ('common', 'ex') if '--ex' in args else ('common',)
    nicks = [a for a in args if not a.startswith('--')] or ['a', 'b', 'c', 'd', 'e']
    eng = new_game(nicks, packs=packs)
    show(eng.drain_effects())
    try:
        while not eng.winner:
            print('\n' + render_table(eng))
            action = prompt(eng, eng.pending)
            try:
                effects = eng.timeout() if action is None else eng.apply(action)
            except IllegalAction as e:
                print(f'非法动作：{e}')
                continue
            show(effects)
    except KeyboardInterrupt:
        print('\n已退出对局')
        return
    print('\n' + render_table(eng))


if __name__ == '__main__':
    main()
