import random


class DeckMaster:
    def __init__(self, deck):
        self.hand = []
        self.deck = deck
        self.trash = Trash()

    # --- draw from deck ---
    def draw_n(self, n):
        for _ in range(n):
            self.draw()
    
    def draw(self):
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
