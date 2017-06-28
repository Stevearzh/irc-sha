from transitions import State

from isha.model.card.basic import sha, shan

STATUS_DICT = {
    'unknown':        State('未知'),
    'normal':         State('正常'),
    'being_sha':      State('被杀'),
    'damage_confirm': State('伤害结算'),
    'dying':          State('濒死'),
    'died':           State('死亡')
}

STATUS = [
    STATUS_DICT['unknown'],
    STATUS_DICT['normal'],
    STATUS_DICT['being_sha'],
    STATUS_DICT['damage_confirm'],
    STATUS_DICT['dying'],
    STATUS_DICT['died'],
]

TRANSITIONS = [
    {
        'trigger': sha.effect,
        'source':  STATUS_DICT['normal'],
        'dest':    STATUS_DICT['being_sha']
    }, {
        'trigger': shan.effect,
        'source':  STATUS_DICT['being_sha'],
        'dest':    STATUS_DICT['normal']
    }
]
