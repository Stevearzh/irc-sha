"""前端共享渲染：把引擎输出的 Effect / 公开状态渲染为中文文本。

Effect 只含公开信息，可直接广播；手牌等私密信息在提示输入时单独展示。
"""

from isha.core.effects import Effect


def render_effect(e: Effect) -> str:
    d = e.data
    match e.kind:
        case 'game_start':
            return f"游戏开始！座次：{' → '.join(d['seats'])}，主公是 {d['king']}"
        case 'turn_start':
            return f"—— 第 {d['turn']} 轮：{d['nick']} 的回合 ——"
        case 'draw':
            return f"{d['nick']} 摸了 {d['count']} 张牌"
        case 'card_used':
            if d['target']:
                return f"{d['nick']} 对 {d['target']} 使用了【{d['label']}】"
            return f"{d['nick']} 使用了【{d['label']}】"
        case 'dodge':
            return f"{d['nick']} 打出【{d['label']}】，闪避成功"
        case 'responded':
            return f"{d['nick']} 打出【{d['label']}】响应"
        case 'negate_used':
            return f"{d['nick']} 打出【{d['label']}】"
        case 'negated':
            return f"【{d['label']}】对 {d['target']} 的效果被抵消"
        case 'snatch':
            if d.get('label'):
                return f"{d['nick']} 顺手牵羊，获得 {d['target']} 的【{d['label']}】"
            return f"{d['nick']} 顺手牵羊，获得 {d['target']} 的一张手牌"
        case 'dismantle':
            return f"{d['nick']} 过河拆桥，{d['target']} 的【{d['label']}】被弃置"
        case 'harvest_reveal':
            return '五谷丰登亮出：' + '、'.join(d['labels'])
        case 'harvest_pick':
            return f"{d['nick']} 选择了【{d['label']}】"
        case 'judge_flip':
            return f"{d['nick']} 的{d['reason']}判定：【{d['label']}】"
        case 'trick_placed':
            return f"【{d['label']}】置入 {d['nick']} 的判定区"
        case 'skip_play':
            return f"{d['nick']} 跳过出牌阶段（{d['reason']}）"
        case 'lightning_move':
            return f"闪电移至 {d['nick']} 的判定区"
        case 'lightning_fizzle':
            return f"【{d['label']}】无人可传，置入弃牌堆"
        case 'equip':
            return f"{d['nick']} 装备了【{d['label']}】"
        case 'unequip':
            return f"{d['nick']} 的【{d['label']}】被替换，置入弃牌堆"
        case 'borrow':
            return f"{d['nick']} 借刀杀人：{d['holder']} 需对 {d['target']} 出杀"
        case 'weapon_gained':
            return f"{d['nick']} 获得了 {d['target']} 的【{d['label']}】"
        case 'guanshi':
            return f"{d['nick']} 弃 2 张牌，强制命中 {d['target']}（贯石斧）"
        case 'renwang':
            return f"【{d['label']}】是黑色的杀，对 {d['nick']} 无效（仁王盾）"
        case 'icesword':
            labels = '、'.join(f"【{l}】" for l in d['labels'])
            return (f"{d['nick']} 发动寒冰剑，防止对 {d['target']} 的伤害，"
                    f"弃置其 {labels}")
        case 'horse_shot':
            return f"{d['nick']} 射掉了 {d['target']} 的【{d['label']}】（麒麟弓）"
        case 'damaged':
            return f"{d['nick']} 受到 {d['amount']} 点伤害（剩余体力 {d['hp']}）"
        case 'dying':
            return f"{d['nick']} 进入濒死状态！"
        case 'peach_used':
            return f"{d['nick']} 对 {d['target']} 使用【{d['label']}】，{d['target']} 回复至 {d['hp']}"
        case 'healed':
            return f"{d['nick']} 回复 1 点体力（当前 {d['hp']}）"
        case 'discard':
            return f"{d['nick']} 弃了 {d['count']} 张牌"
        case 'reshuffle':
            return '弃牌堆洗回牌堆'
        case 'died':
            return f"!! {d['nick']} 阵亡，身份是【{d['identity']}】"
        case 'reward':
            return f"{d['nick']} 击杀反贼，摸 {d['count']} 张牌"
        case 'punish':
            return f"{d['nick']} 误杀忠臣，弃光所有牌（共 {d['count']} 张）"
        case 'game_over':
            return f"** 游戏结束，{d['winner']} 获胜！ **"
        case 'turn_end':
            return ''
        case _:
            return f'[{e.kind}] {d}'


def render_table(engine) -> str:
    cur = engine.pending.player if engine.pending else None
    lines = [f'牌堆 {len(engine.deck)} / 弃牌堆 {len(engine.discard_pile)}']
    for p in engine.players:
        mark = ' ' if p.alive else '×'
        judge = f"  判定区:{' '.join(c.label for c in p.judgement)}" if p.judgement else ''
        equip = f"  装备:{' '.join(c.detail for c in p.equips())}" if p.equips() else ''
        dist = ''
        if cur and p.nick != cur and p.alive and engine.player(cur).alive:
            dist = f'  距当前 {engine.distance(cur, p.nick)}'
        # 游戏结束时亮明所有身份
        ident = p.identity if engine.winner else p.public_identity()
        lines.append(
            f'{mark} {p.nick:<8} 体力 {p.hp}/{p.max_hp}  身份 {ident}'
            f'  手牌 {len(p.hand)} 张{dist}{judge}{equip}')
    return '\n'.join(lines)


def render_hint(ask) -> str:
    """响应窗口的操作提示语（CLI 与 Web 前端共用）。"""
    match ask.kind:
        case 'play':
            return '出牌阶段：选择要出的牌，或结束出牌'
        case 'respond_sha':
            return f"{ask.data['source']} 对你出杀（{ask.data['sha']}）：出闪或不出"
        case 'respond_aoe':
            d = ask.data
            return f"{d['source']} 使用了{d['trick']}：出{d['response']}或不出"
        case 'duel':
            return f"与 {ask.data['other']} 决斗中：出杀，否则受到 1 点伤害"
        case 'negate':
            d = ask.data
            hint = f"{d['trick']}（目标 {d['target']}）即将生效：出无懈可击或不出"
            if 'response_name' in d:   # 被询问者即目标本人：提示其响应牌数量
                hint += f"；你手上有【{d['response_name']}】×{len(d['response_cards'])}"
            return hint
        case 'harvest':
            return '五谷丰登：从亮出的牌中选择一张'
        case 'choose_card':
            d = ask.data
            return f"选择 {d['target']} 的一张牌（手牌为暗牌，按位置盲选）"
        case 'choose_player':
            return f"借刀杀人：选择 {ask.data['holder']} 要出杀的目标"
        case 'borrow_sha':
            d = ask.data
            hint = f"借刀杀人：对 {d['target']} 出杀，否则武器交给 {d['source']}"
            if d.get('zhangba'):
                hint += '（丈八蛇矛：可打出两张手牌当杀）'
            return hint
        case 'chase':
            return f"青龙偃月刀：可对 {ask.data['target']} 再出一张杀"
        case 'guanshi':
            return f"贯石斧：弃 2 张牌强制命中 {ask.data['target']}，或放弃"
        case 'icesword':
            if ask.data.get('optional'):
                return (f"寒冰剑：可依次弃置 {ask.data['target']} 的两张牌以防止伤害"
                        f"（手牌为暗牌按位置盲选），或放弃并正常造成伤害")
            return f"寒冰剑：再弃置 {ask.data['target']} 的一张牌"
        case 'qilin':
            return f"麒麟弓：可弃置 {ask.data['target']} 的一匹马"
        case 'peach':
            return f"{ask.data['target']} 濒死：出桃或不出"
        case 'discard':
            return f"弃牌阶段：需弃 {ask.data['count']} 张"
        case _:
            return ask.kind
