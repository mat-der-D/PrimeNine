from enum import Enum, auto
import pandas as pd
import random
from . card import Card, TacticsCard, VSCard, PlayerCard
from . card import Position


# **************
# * GamePlayer *
# **************
class GamePlayer:
    def __init__(self, deck_master, deck_field, team_status):
        self.deck_master = deck_master
        self.deck_field = deck_field
        self.team_status = team_status

    # --- deck master ---
    def draw(self, n=1):
        self.deck_master.draw(n)

    # --- deck field ---
    def refresh_deck_field(self):
        trash = self.deck_master.trash
        self.deck_field.refresh(trash)

    # tactics card
    def set_tactics_card(self, card, is_open):
        self.deck_field.tactics_zone.set_card(card, is_open)

    # v.s. card
    @property
    def vs_card(self):
        return self.deck_field.vs_card
    
    def set_vs_card(self, card):
        self.deck_field.vs_zone.set_card(card)

    def open_vs_card(self):
        self.deck_field.vs_zone.open_all()
        
    # sp-combo
    def set_sp_combo(self, card, batter):
        self.deck_field.sp_combo_zone.set_card(card, batter)
        self.draw() # <-- Should it be implemented here?
        
    # --- team status ---
    def increment_pitch_inning(self):
        self.team_status.pitch_innings += 1

    @property
    def pitcher(self):
        return self.team_status.pitcher

    def nth_batter(self, n):
        return self.team_status.nth_batter(n)
        
        
# **************
# * DeckMaster *
# **************
class DeckMaster:
    def __init__(self, deck):
        self.hand = []
        self.deck = deck
        self.trash = Trash()

    # --- draw from deck ---
    def draw(self, n=1):
        for _ in range(n):
            self._draw()
    
    def _draw(self):
        if len(self.deck) == 0:
            if len(self.trash) == 0:
                raise Exception("cannot draw")
            self.return_trash_to_deck()

        self.hand.append(self.deck.pop(0))

    def return_trash_to_deck(self):
        self.trash.shuffle()
        self.deck.extend(self.trash)
        self.trash.clear()    
        
    # --- from hand ---
    def pick_up_from_hand(self, idx):
        return self.hand.pop(idx)

    # --- trash card ---
    def trash(self, card):
        self.trash.append(card)
    
    # --- place card to field ---
    def set_card(self, card, zone, is_open=None):
        if isinstance(zone, TacticsZone):
            if is_open is None:
                raise Exception("designate 'is_open'")
            zone.set_card(card, is_open)
        if isinstance(zone, (PlayZone, SPComboZone)):
            zone.set_card(card)
    
        
class Deck(list):
    def __init__(self, deck_list):
        super().__init__(deck_list)
        self.shuffle()

    def shuffle(self):
        random.shuffle(self)

        
class Trash(list):
    def shuffle(self):
        random.shuffle(self)


# *************
# * DeckField *
# *************
# ??? some other namings ??? (not 'field')
class DeckField:
    def __init__(self):
        self.tactics_zone = TacticsZone()
        self.vs_zone = VSZone()
        self.sp_combo_zone = SPComboZone()

    def refresh(self, trash):
        """
        call this at the time of 'change'
        """
        # <-- check each tactics card if it can be trashed
        self.vs_zone.trash_all(trash)
        self.sp_combo_zone.trash_all(trash)

    @property
    def vs_card(self):
        if len(self.vs_zone) == 0:
            return None
        else:
            return self.vs_zone[0][0]

    
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

    def trash(self, trash_, idx):
        card = self.pop(idx)[0]
        card.refresh()
        trash_.append(card)
            
    def trash_all(self, trash_):
        for card, _ in self:
            card.refresh()
            trash_.append(card)
        self.clear()

        
class TacticsZone(Zone):
    pass
        

class VSZone(Zone):
    def set_card(self, card):
        super().set_card(card, is_open=False)


class SPComboZone(Zone):
    def set_card(self, card, batter):
        if card.id != batter.id:
            raise Exception(
                "card No. of set card and the one "
                "at batter box must be the same"
            )
        super().set_card(card, is_open=True)


# **************
# * TeamStatus *
# **************
class TeamStatus:
    def __init__(self, df_status):
        self.df_status = df_status
        self.pitch_innings = 0

    @property
    def pitcher(self):
        card = self.df_status[
            self.df_status.position == Position.PITCHER
        ].card.iloc[0]
        return card
    
    def update_penalty(self):
        self.df_status.reset_index(drop=True, inplace=True)
        
        card_dict = self.df_status.card.to_dict()
        position_dict = self.df_status.position.to_dict()
        def idx_to_penalty(idx):
            card = card_dict[idx]
            position = position_dict[idx]
            return not card.is_defensible(position)

        self.df_status.is_penalty \
            |= self.df_status.index.map(idx_to_penalty)

    def nth_batter(self, n):
        if n not in range(9):
            raise ValueError("n must be in range(9)")
        # <-- validation::
        #   set(df_status.order) == set(range(9))        
        batter = self.df_status[
            self.df_status.order == n
        ].card.iloc[0]
        return batter
