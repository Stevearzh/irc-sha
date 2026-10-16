import random

from isha.dict.identity import IDENTITY


def gen_id_list(num: int, rng: random.Random | None = None) -> list[str]:
    rng = rng or random
    if num == 5:   # 1 king, 1 minister, 2 rebel and 1 traitor
        ids = [
            IDENTITY['king'],
            IDENTITY['minister'],
            IDENTITY['rebel'], IDENTITY['rebel'],
            IDENTITY['traitor']
        ]
    elif num == 8:   # 1 king, 2 minister, 4 rebel and 1 traitor
        ids = [
            IDENTITY['king'],
            IDENTITY['minister'], IDENTITY['minister'],
            IDENTITY['rebel'], IDENTITY['rebel'], IDENTITY['rebel'], IDENTITY['rebel'],
            IDENTITY['traitor']
        ]
    else:
        raise ValueError('unsupported player size')

    rng.shuffle(ids)
    return ids
