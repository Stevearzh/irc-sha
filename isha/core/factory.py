import csv
from functools import reduce

from isha.model.card import RECIPE as CARD_RECIPE
from isha.dict.card import CARD_SUIT

def card_generator(path, pack_list, recipe=CARD_RECIPE, filters=list(CARD_RECIPE.keys())):
    result = []
    list(map(lambda pack: result.extend(card_loader(path + pack + '.csv')), pack_list))

    result = list(filter(lambda model: model_available(model, filters), result))
    result = list(map(lambda model: recipe[model['name']](model['suit'], model['point']), result))

    return result

def card_loader(source):
    result = []
    with open (source) as f:
        reader = csv.DictReader(f)
        for row in reader:
            result.append({
                'suit': CARD_SUIT[row['suit']],
                'point': row['point'],
                'name': row['name']
            })
    return result

def model_available(model, filters):
    return reduce(lambda r, name: r or name == model['name'], filters, False)
