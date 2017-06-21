#!/usr/bin/env python3

from isha.core.table import table
from isha.model.event import game_start

PATH = './package/card/'

n = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
t = table(PATH, n)
p = t.players()[len(n) - 1]

game_start(t)

print('Table\'s position: ' + ' '.join(t.show()))
print('Distance between a and b is: ' + str(t.distance('a', 'b')))
print('Last player has cards: ' + ', '.join(list(map(lambda card: card.suit() + card.point() + card.name(), p.card()))) + ' on his hand.')
