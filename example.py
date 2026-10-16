"""无交互演示：固定种子开一局 5 人局，由简单策略自动打到结束。

策略：出牌阶段能打就打（见杀出杀、残血吃桃），被杀必出闪，濒死必出桃。
运行：python example.py
"""

from isha.core.actions import Pass, PlayCards
from isha.game import new_game
from isha.game.render import render_effect, render_table


def auto_action(eng, ask):
    if ask.kind == 'play':
        options = ask.data['options']
        if options:
            cid, targets = next(iter(options.items()))
            return PlayCards(ask.player, (cid,), targets[0] if targets else None)
        return Pass(ask.player)
    if ask.kind == 'negate':
        return Pass(ask.player)          # 演示：不出无懈可击
    if ask.kind == 'harvest':
        return PlayCards(ask.player, (ask.data['revealed'][0][0],))
    if ask.kind == 'choose_player':
        return PlayCards(ask.player, (), ask.data['targets'][0])
    if ask.kind == 'guanshi':
        return Pass(ask.player)          # 演示：不强制命中
    if ask.kind == 'respond_sha' and not ask.data.get('cards') \
            and ask.data.get('armor'):
        return PlayCards(ask.player, ())   # 八卦阵判定
    if ask.data.get('cards'):
        return PlayCards(ask.player, (ask.data['cards'][0][0],))
    return ask.default   # discard


def main():
    eng = new_game(['阿瞒', '玄德', '仲谋', '本初', '奉先'], seed=42)
    show(eng.drain_effects())

    while not eng.winner:
        ask = eng.pending
        print(f'\n[等待 {ask.player} 行动：{ask.kind}]')
        show(eng.apply(auto_action(eng, ask)))

    print('\n' + render_table(eng))


def show(effects):
    for e in effects:
        line = render_effect(e)
        if line:
            print(line)


if __name__ == '__main__':
    main()
