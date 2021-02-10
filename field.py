from copy import deepcopy

class Field:
    def __init__(self):
        self.mound = None
        self.batter_box = None # [Card, is_right]
        self.runners = [None, None, None] # 1B, 2B, 3B

        # --- zones ---
        self.tactics_zones = (TacticsZone(), TacticsZone())
        self.play_zones = (PlayZone(), PlayZone())
        self.sp_combo_zones = (SPComboZone(), SPComboZone())

    
    def set_card_to_zone(self card, zone, is_open=None):
        if isinstance(zone, TacticsZone):
            if is_open is None:
                raise TypeError("designate 'is_open'")
            zone.set_card(card, is_open)
        if isinstance(zone, (PlayZone, SPComboZone)):
            zone.set_card(card)

    def step_into_batter_box(self, card, is_right):
        self.batter_box = [deepcopy(card), is_right]

    def take_mound(self, card):
        self.mound = deepcopy(card)
        
        
class Zone(list):
    def __init__(self):
        super().__init__()

    def set_card(self, card, is_open):
        self.append([card, is_open])

    def open(self, idx):
        self[idx][1] = True

    def open_all(self):
        for card_flag in self:
            card_flag[1] = True

    def trash_all(self, trash):
        for card_flag in self:
            trash.append(card_flag[0])
        self.clear()


class TacticsZone(Zone):
    pass


class PlayZone(Zone):
    def set_card(self, card):
        super().set_card(card, is_open=False)


class SPComboZone(Zone):
    def set_card(self, card):
        super().set_card(card, is_open=True)
