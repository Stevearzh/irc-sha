import random

from sha.dict.identity import IDENTITY

def gen_id_list(num):
    if num == 5:   # 1 king, 1 minister, 2 rebel and 1 traitor
        list = [
            IDENTITY['king'],
            IDENTITY['minister'],
            IDENTITY['rebel'], IDENTITY['rebel'],
            IDENTITY['traitor']
        ]
    elif num == 8:   # 1 king, 2 minister, 4 rebel and 1 traiter
        list = [
            IDENTITY['king'],
            IDENTITY['minister'], IDENTITY['minister'],
            IDENTITY['rebel'], IDENTITY['rebel'], IDENTITY['rebel'], IDENTITY['rebel'],
            IDENTITY['traitor']
        ]
    else:
        raise ValueError('unsupported player size')

    random.shuffle(list)
    return list
