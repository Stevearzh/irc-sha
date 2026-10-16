"""本地 Web 热座前端：在浏览器里手动测试体验。

运行：
    python -m isha.game.web [--port 8000] [--timeout 60] [--idle-timeout 300]
然后打开 http://127.0.0.1:8000

热座模式：一个浏览器轮流操作所有玩家；只展示当前应行动玩家的手牌与身份。
零第三方依赖（标准库 http.server），引擎通过 JSON API 驱动。

对局生命周期：默认无对局，点击"新开局"才开始；所有前端请求都会刷新
活跃时间，超过 idle-timeout 秒无人连接则自动关闭对局。
"""

import argparse
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from isha.core.actions import DiscardCards, Pass, PlayCards
from isha.core.engine import Engine, IllegalAction

from . import new_game
from .render import render_effect, render_hint

PAGE = Path(__file__).with_name('web_page.html').read_text(encoding='utf-8')

NICKS = {
    5: ['甲', '乙', '丙', '丁', '戊'],
    8: ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛'],
}


class Game:
    """引擎 + 日志 + 响应超时 + 闲置回收的线程安全包装。

    - 响应超时：每个响应窗口建立时启动计时器，超时未行动则执行默认动作。
      timeout_secs=0 关闭。
    - 闲置回收：超过 idle_timeout 秒没有任何前端请求则关闭对局。
      idle_timeout=0 关闭。
    """

    def __init__(self, timeout_secs: int = 60, idle_timeout: int = 300):
        self.lock = threading.Lock()
        self.timeout_secs = timeout_secs
        self.idle_timeout = idle_timeout
        self._timer: threading.Timer | None = None
        self.deadline: float | None = None
        self.engine: Engine | None = None      # 默认无对局
        self.log: list[str] = []
        self.last_activity = time.time()

    # ---------- 生命周期 ----------

    def start(self, size: int, seed: int | None = None):
        self.engine = new_game(NICKS[size], seed=seed)
        self.log = [line for e in self.engine.drain_effects()
                    if (line := render_effect(e))]
        self.last_activity = time.time()
        self._arm_timer()

    def close(self):
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None
        self.deadline = None
        self.engine = None

    def touch(self):
        """每次前端请求调用：先回收闲置对局，再刷新活跃时间。"""
        if self.engine is not None and self._idle_expired():
            self.log.append('（长时间无人连接，对局已自动关闭）')
            self.close()
        self.last_activity = time.time()

    def _idle_expired(self) -> bool:
        return self.idle_timeout > 0 \
            and time.time() - self.last_activity > self.idle_timeout

    # ---------- 响应超时 ----------

    def _arm_timer(self):
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None
        self.deadline = None
        if self.engine is None:
            return
        if self.timeout_secs > 0 and self.engine.pending is not None \
                and not self.engine.winner:
            self.deadline = time.time() + self.timeout_secs
            self._timer = threading.Timer(self.timeout_secs, self._auto_timeout)
            self._timer.daemon = True
            self._timer.start()

    def _auto_timeout(self):
        with self.lock:
            if self.engine is None or self.engine.pending is None \
                    or self.engine.winner:
                return
            if self._idle_expired():   # 无人观战就不自己打下去了
                self.log.append('（长时间无人连接，对局已自动关闭）')
                self.close()
                return
            self.log.append(f"（{self.engine.pending.player} 超时，执行默认动作）")
            self.timeout()

    def timeout(self):
        if self.engine is not None and self.engine.pending is not None:
            self._record(self.engine.timeout())
        self._arm_timer()

    # ---------- 动作 ----------

    def apply(self, body: dict):
        eng = self.engine
        if eng is None:
            raise IllegalAction('当前没有进行中的对局，请先开局')
        ask = eng.pending
        if ask is None:
            raise IllegalAction('当前无需操作')
        match body.get('type'):
            case 'pass':
                action = Pass(ask.player)
            case 'play':
                action = PlayCards(ask.player, tuple(body.get('cids', [])),
                                   body.get('target'))
            case 'discard':
                action = DiscardCards(ask.player, tuple(body.get('cids', [])))
            case _:
                raise IllegalAction('未知动作类型')
        self._record(eng.apply(action))
        self._arm_timer()

    def _record(self, effects):
        self.log.extend(line for e in effects if (line := render_effect(e)))

    # ---------- 状态 ----------

    def state(self) -> dict:
        if self.engine is None:
            return {'active': False, 'log': self.log[-100:]}
        eng = self.engine
        ask = eng.pending
        cur = ask.player if ask else None
        cur_alive = cur and eng.player(cur).alive
        return {
            'active': True,
            'winner': eng.winner,
            'turn': eng.turn_no,
            'phase': eng.phase,
            'deck': len(eng.deck),
            'discard': len(eng.discard_pile),
            'timeout_remaining': (max(0, round(self.deadline - time.time()))
                                  if self.deadline else None),
            # 当前行动者的真实身份（热座模式仅自己可见自己身份）
            'you': None if not cur else
                   {'nick': cur, 'identity': eng.player(cur).identity},
            'players': [{
                'nick': p.nick,
                'seat': p.seat,
                'hp': p.hp,
                'max_hp': p.max_hp,
                # 游戏结束时亮明所有身份
                'identity': p.identity if eng.winner else p.public_identity(),
                'alive': p.alive,
                'hand_count': len(p.hand),
                'judgement': [c.label for c in p.judgement],   # 判定区为公开信息
                'equips': [c.detail for c in p.equips()],      # 装备区为公开信息
                # 与当前行动玩家的方向距离（含马匹修正）
                'distance': (eng.distance(cur, p.nick)
                             if cur_alive and p.alive and p.nick != cur else None),
            } for p in eng.players],
            'pending': None if ask is None else {
                'player': ask.player,
                'kind': ask.kind,
                'hint': render_hint(ask),
                'count': ask.data.get('count'),
                'armor': ask.data.get('armor', False),      # 可八卦阵判定
                'targets': ask.data.get('targets'),         # choose_player 可选目标
                'zhangba': ask.data.get('zhangba'),         # 丈八蛇矛可选目标
            },
            'hand': self._hand(eng, ask),
            'log': self.log[-100:],
        }

    def _hand(self, eng: Engine, ask) -> list[dict]:
        """当前应行动玩家的可选牌（含每张牌此刻是否可出/可选）。

        harvest 窗口展示的是亮出的牌而非手牌；choose_card 展示目标的牌。
        """
        if ask is None:
            return []
        if ask.kind == 'harvest':
            return [{'cid': cid, 'label': label, 'playable': True}
                    for cid, label in ask.data['revealed']]
        if ask.kind == 'choose_card':
            # 顺手/过河的选牌窗口：label 为 None 的是目标的手牌（暗牌）
            return [{'cid': cid, 'label': label or '暗牌', 'playable': True,
                     'face_down': label is None}
                    for cid, label in ask.data['cards']]
        if ask.kind == 'choose_player':
            return []   # 目标在玩家列表上点击，无牌可选
        p = eng.player(ask.player)
        if ask.kind == 'play':
            options = ask.data['options']
            multi = ask.data.get('multi', {})
            return [{'cid': c.cid, 'label': c.label,
                     'playable': c.cid in options,
                     'targets': options.get(c.cid, []),
                     'multi': multi.get(c.cid, 1)}   # 方天画戟：可多选目标
                    for c in p.hand]
        if ask.kind in ('discard', 'guanshi'):
            allowed = {c.cid for c in p.hand}
        else:   # respond_sha / peach / negate / respond_aoe / duel / chase / qilin
            allowed = {cid for cid, _ in ask.data.get('cards', [])}
        return [{'cid': c.cid, 'label': c.label, 'playable': c.cid in allowed}
                for c in p.hand]


class Handler(BaseHTTPRequestHandler):
    game = Game()

    def do_GET(self):
        with self.game.lock:
            self.game.touch()
            if self.path == '/':
                self._send(200, PAGE.encode(), 'text/html; charset=utf-8')
            elif self.path == '/api/state':
                self._json(200, self.game.state())
            else:
                self._send(404, b'', '')

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get('Content-Length') or 0))
        try:
            payload = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self._json(400, {'error': '请求不是合法 JSON'})
            return

        with self.game.lock:
            self.game.touch()
            try:
                if self.path == '/api/new':
                    self.game.start(int(payload.get('size', 5)),
                                    payload.get('seed'))
                elif self.path == '/api/action':
                    self.game.apply(payload)
                elif self.path == '/api/timeout':
                    self.game.timeout()
                else:
                    self._send(404, b'', '')
                    return
            except (IllegalAction, KeyError, ValueError, StopIteration) as e:
                self._json(400, {'error': str(e) or '非法操作'})
                return
            self._json(200, self.game.state())

    def _json(self, code: int, obj: dict):
        self._send(code, json.dumps(obj, ensure_ascii=False).encode(),
                   'application/json; charset=utf-8')

    def _send(self, code: int, data: bytes, content_type: str):
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):   # 静默访问日志
        pass


def main():
    parser = argparse.ArgumentParser(description='irc-sha 本地 Web 热座前端')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--timeout', type=int, default=60,
                        help='响应窗口超时秒数，超时执行默认动作；0 关闭（默认 60）')
    parser.add_argument('--idle-timeout', type=int, default=300,
                        help='无连接自动关闭对局的秒数；0 关闭（默认 300）')
    args = parser.parse_args()

    Handler.game = Game(timeout_secs=args.timeout,
                        idle_timeout=args.idle_timeout)
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f'irc-sha web 前端已启动：http://{args.host}:{args.port}')
    print(f'响应超时 {args.timeout}s / 闲置回收 {args.idle_timeout}s'
          '（0 表示关闭对应功能）')
    print('热座模式：所有玩家在此页面轮流操作。Ctrl-C 停止。')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
