"""防具：八卦阵（被杀/万箭时可判定代替出闪，见 card/base.py 的 dodge_window）。"""

from ..base import EquipRule


class ArmorRule(EquipRule):
    slot = 'armor'
