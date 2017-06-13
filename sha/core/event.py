EVENT = {
    'unknown': 'unknown',

    'card_shuffle': 'card_shuffle',

    'game_start': 'game_start',
    'game_end': 'game_end',

    'turn_start': 'turn_start',
    'turn_end': 'turn_end',

    'parse_judge': 'parse_judge',
    'parse_start': 'parse_start',
    'card_deal': 'card_deal',
    'parse_process': 'parse_process',
    'parse_end': 'parse_end',
    'card_discard': 'card_discard',
    'card_discarded': 'card_discarded',
    'parse_skip': 'parse_skip',

    'card_used': 'card_used',
    'target_choose': 'target_choose',
    'card_effected': 'card_effected',
    'card_finished': 'card_finished',
    'card_canceled': 'card_canceled',
    'card_responsed': 'card_responsed',

    'damage_confirm': 'damage_confirm',
    'damaged': 'damaged',

    'hp_recovered': 'hp_recovered',
    'hp_lost': 'hp_lost',
    'hp_lost_effect': 'hp_lost_effect',

    'player_is_dying': 'player_is_dying',
    'player_not_die': 'player_not_die',
    'player_ask_peach': 'player_ask_peach',
    'player_ask_peach_done': 'player_ask_peach_done',
    'player_died': 'player_died',
    'game_over_judge': 'game_over_judge',
    'player_eliminate': 'player_eliminate'
}

class event:
    def __init__(self, type, effect):
        self.__type   = type
        self.__effect = effect

        try:
            list(EVENT.values()).index(self.__type)
        except Exception as e:
            self.__type = EVENT['unknown']

    def show_type(self):
        return self.__type
