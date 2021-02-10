from enum import Enum, Flag, auto
import random

class Game:
    def __init__(self, players
                 max_inning, max_extra_inning, is_dh):
        self.scores = [0, 0]
        self.out_count = 0
        self.is_bottom = False # top/bottom === OMOTE/URA
        self.inning = 0
        self.next_batter = [0, 0]
        self.players = players # (GamePlayer, GamePlayer)

        self.field = Field()
        
        self.MAX_INNING = max_inning
        self.MAX_EXTRA_INNING = max_extra_inning
        self.IS_DH = is_dh

        
    def playball_and_return_winner(self):
        return StartInningPhase.next_inning(self)


# *** Phases ***
class StartGamePhase:
    @staticmethod
    def init_hand(game):
        for player in game.players:
            cards = player.deck.draw_n(5)
            player.hand

class StartInningPhase:
    @staticmethod
    def next_inning(game):
        game.inning += 1
        game.is_bottom = False
        return StartTopBottomInningPhase.play(game)
    
    
class StartTopBottomInningPhase:
    @staticmethod
    def play(game):
        # <-- set position (not implemented yet)
        game.field.pitcher \
            = game.players[game.is_bottom].team.pitcher
        return AtBatPhase.play(game)
    
    
class AtBatPhase: # DASEKI
    @staticmethod
    def play(game):
        pass
    
    class BatterSetAction:
        pass
    
    class PrePitchAction:
        pass
    
    class PitchAction:
        pass

    class PostPitchAction:
        pass
    
    class GaugeCheckAction:
        pass
    
    class PostGaugeCheckAction:
        pass
    
    class FinishAtBatAction:
        pass


class FinishTopBottomInningPhase:
    @staticmethod
    def play(game):
        game.out_count = 0
        game.runner = [None]*3
        # <-- discard hands (not implemented yet)
        game.players[not game.is_bottom].team.pitch_inning += 1
        if game.is_bottom:
            return game.FinishInningPhase.next_inning(game)
        else:
            game.is_bottom = True
            return StartTopBottomInningPhase.play(game)
        

class FinishInningPhase:
    @staticmethod
    def judge_game_set(game):
        if game.inning < game.max_inning:
            return StartInningPhase.next_inning(game)
        else:
            return FinishGamePhase.winner(game)
        
        
class FinishGamePhase:
    @staticmethod
    def winner(game):
        if game.scores[0] > game.scores[1]:
            return 0
        elif game.scores[0] < game.scores[1]:
            return 1
        elif game.inning < game.max_extra_inning:
            return StartInningPhase.next_inning(game)
        else:
            return None
    
# *** Phases END ***
        
    
class GamePlayer:
    def __init__(self, team, deck_trash):
        self.hand = Hand()
        self.deck_trash = deck_trash
        self.team = team

    def draw_n(self, n):
        cards = self.deck_trash.draw_n(n)
        self.hand.extend(cards)

    def trash_n(self, idx_list):
        for idx in sorted(set(idx_list), reverse=True):
            self.trash(idx)
        
    def trash(self, idx_hand):
        card_to_trash = self.hand.pick_up(idx_hand)
        self.deck_trash.trash.append(card_to_trash)
        

class DeckTrash:
    def __init__(self, card_list):
        self.deck = card_list
        self.trash = []
        self.shuffle()

    def draw_n(self, n):
        drawn_cards = [
            self.draw() for _ in range(n)
        ]
        return drawn_cards
        
    def draw(self):
        if self.deck == []:
            if self.trash == []:
                raise Exception("cannot draw")
            self.return_trash_to_deck()        
        return self.deck.pop(0)
        
    def shuffle(self):
        random.shuffle(self.deck)

    def return_trash_to_deck(self):
        random.shuffle(self.trash)
        self.deck.extend(self.trash)
        self.trash = []


class Hand(list):
    def pick_up(self, idx):
        return self.pop(idx)
        
        

class Team:
    def __init__(self, order: Order, pitcher, reserve):
        """
        order:
          [
            {card: Saeki, position: Position.INFIELDER},
            {card: Kubo, position: Position.OUTFIELDER},
            ...
          ]
        """
        self.order = order
        self.pitcher_condition = PitcherCondition(pitcher)
        self.reserve = reserve # HIKAE
        self.locker_room = []
        

class Order(list):
    # ToDo: validation
    def __init__(self, order_json):
        """
        order_json = [
            {"player": PlayerCard, "position": Position.SOME},
            {"player": PlayerCard, "position": Position.SOME},
            ...
        ]
        """
        super().__init__(order_json)


    def players_with_position(self, position):
        players = [
            d["player"]
            for d in self
            if d["position"] == position
        ]
        return players

    def pitcher(self):
        pitchers = self.players_with_position(Position.PITCHER)
        return pitchers[0]

    def catcher(self):
        catchers = self.players_with_position(Position.CATCHER)
        return catchers[0]

    def infielders(self):
        return self.players_with_position(Position.INFIELDER)

    def outfielders(self):
        return self.players_with_position(Position.OUTFIELDER)

    def dh(self):
        dhs = self.players_with_position(Position.DH)
        return dhs[0]
    
class PitcherCondition:
    def __init__(self, pitcher):
        self.pitcher = pitcher
        self.innings = 0


class Field:
    def __init__(self):
        self.pitcher = None
        self.batter = None
        self.runners = [None, None, None]

        self.sp_combo = None
        


class Position(Enum):
    PITCHER = auto()
    CATCHER = auto()
    INFIELDER = auto()
    OUTFIELDER = auto()
    DH = auto()

    
    




class Course(Enum):
    CENTER = auto()
    HIGH = auto()
    LOW = auto()
    LEFT = auto()
    RIGHT = auto()


class MeetShotPoint(Enum):
    NULL = auto()
    FILL = auto()
    STAR = auto()


class MeetShotPoints(dict):
    def __init__(self):
        super().__init__()



    
class Effect:
    pass


class Card:
    def __init__(self, id):
        self.id = id


class PlayerCard(Card):
    
    class PlayerType(Flag):
        STARTER = auto()
        RELIEVER = auto()
        CATCHER = auto()
        INFIELDER = auto()
        OUTFIELDER = auto()
    
    def __init__(self, id, power, draw):
        super().__init__(id)
        self.power = power
        self.draw = draw

        
class TacticsCard(Card):
    def __init__(id, cost, tactics_type, effect):
        super().__init__(id)
        self.cost = cost
        self.tactics_type = tactics_type
        self.effect = effect


class VSCard(Card):
    def __init__(self, id, course, pw_off, pw_def):
        super().__init__(id)
        self.course = course
        self.pw_off = pw_off
        self.pw_def = pw_def
