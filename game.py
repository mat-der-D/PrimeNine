from copy import deepcopy
import numpy as np
from . card import Card, PlayerCard, TacticsCard, VSCard


class Rule:
    def __init__(self, max_inning, max_extra_inning, is_dh):
        self.max_inning = max_inning
        self.max_extra_inning = max_extra_inning
        self.id_dh = is_dh


class ScoreBoard:
    def __init__(self):
        self.board = [[], []] # top, bottom
        self.total_score = [0, 0]

    def new_inning(self, game):
        self.board[game.is_bottom].append(None)

    def calc_total_score(self):
        self.total_score = [
            sum(filter(None, each_score))
            for each_score in self.board
        ]

    def add_score(self, n, game):
        board = self.board[game.is_bottom]
        if board[-1] is None:
            board[-1] = n
        else:
            board[-1] += n
        self.calc_total_score()

    def fill_zero(self, game):
        self.add_score(0, game)
        
    def winning_team(self):
        if self.total_score[0] > self.total_score[1]:
            return 0
        elif self.total_score[0] < self.total_score[1]:
            return 1
        else:
            return None


class Field:
    def __init__(self):
        self.mound = None
        self.batter_box = None
        self.runners = [None, None, None]

    @property
    def batter(self):
        return self.batter_box[0]
        
    def refresh(self):
        """
        call this at the time of 'change'
        """
        self.__init__()

    def set_mound(self, pitcher):
        self.mound = pitcher
        
    def set_batter(self, batter, is_right):
        self.batter_box = [batter, is_right]
        

class Game:
    def __init__(self, home_player, visitor_player, rule):

        self.score_board = ScoreBoard()
        self.out = None
        self.is_bottom = None # top:0, bottom:1
        self.inning = None
        self.next_batter = [None, None]

        self.players = [visitor_player, home_player]
        self.field = Field()

        # --- game rules ---
        self.RULE = rule
        # max_inning, max_extra_inning, is_dh, etc...
        
    def next_batter_idx(self):
        """
        This method should be implemented by TeamStatus...
        """
        next_idx = self.next_batter[self.is_bottom]
        self.next_batter[self.is_bottom] = (next_idx + 1) % 9
        return next_idx
        
    def playball(self):
        try:
            StartGamePhase.execute(self)
        except GameSet:
            pass # <-- jump to game set phase

    # --- inning ---
    def is_final_inning(self):
        return game.inning >= self.RULE.max_inning

    def can_extend(self):
        return game.inning < self.RULE.max_extra_inning

    def increment_pitch_inning(self):
        def_player = self.players[not self.is_bottom]
        def_player.increment_pitch_inning()
    
    # --- score board ---
    def extend_score_board(self):
        self.score_board.new_inning(self)

    def add_score(self, n):
        self.score_board.add_score(n, self)

    def fill_zero_score(self):
        self.score_board.fill_zero(self)

    def winning_team(self):
        return self.score_board.winning_team()

    # --- players ---
    @property
    def offense_player(self):
        return self.players[self.is_bottom]

    @property
    def defense_player(self):
        return self.players[not self.is_bottom]
    

# *************
# * Exception *
# *************
class GameSet(Exception):
    """
    raise GameSet when the game-set condition is satisfied
    """
    pass
    

# **********
# * Phases *
# **********
class Phase:
    @classmethod
    def execute(cls, game):
        cls.playing(game)
        cls.next_phase().execute(game)

    @staticmethod
    def playing(game):
        raise NotImplementedError()
    
    @staticmethod
    def next_phase(game):
        raise NotImplementedError()


class StartGamePhase(Phase):
    @staticmethod
    def playing(game):
        game.inning = 0
        game.next_batter = [0, 0]
        for player in game.players:
            player.draw(5)

    @staticmethod
    def next_phase(game):
        return StartInningPhase
    

class StartInningPhase(Phase):
    @staticmethod
    def playing(game):
        game.inning += 1
        game.is_bottom = False

    @staticmethod
    def next_phase(game):
        return StartTopBottomInningPhase
    

class StartTopBottomInningPhase(Phase):
    @staticmethod
    def playing(game):
        game.out = 0
        game.extend_score_board()
        # <-- position validation (in case of pinch hitter)
        # <-- change players or positions if needed

    @staticmethod
    def next_phase(game):
        return AtBatPhase


class AtBatPhase(Phase):
    @staticmethod
    def playing(game):
        # <--- goto ***Action class
        pass

    @staticmethod
    def next_phase(game):
        return FinishTopBottomInningPhase


class FinishTopBottomInningPhase(Phase):
    @staticmethod
    def playing(game):
        game.fill_zero_score()
        game.field.refresh()
        # <-- discard hands (not implemented yet)
        game.increment_pitch_inning()
        
    @staticmethod
    def next_phase(game):
        if game.is_bottom:
            return FinishInningPhase
        else:
            if game.is_final_inning() and game.winning_team() == 1:
                raise GameSet
            game.is_bottom = True
            return StartTopBottomInningPhase


class FinishInningPhase(Phase):
    @staticmethod
    def playing(game):
        # <-- check tactics card
        pass

    @staticmethod
    def next_phase(game):
        if not game.is_final_inning():
            return StartInningPhase
        elif game.winning_team() is not None:
            raise GameSet
        elif game.can_extend():
            return StartInningPhase
        else:
            raise GameSet
        
        
# class FinishGamePhase:
#     @staticmethod
#     def winner(game):
#         if game.scores[0] > game.scores[1]:
#             return 0
#         elif game.scores[0] < game.scores[1]:
#             return 1
#         elif game.inning < game.max_extra_inning:
#             return StartInningPhase.next_inning(game)
#         else:
#             return None


# ******************
# * At-Bat Actions *
# ******************
class AtBatResult(Enum):
    STRIKE_OUT = auto()
    INFIELD_GROUNDER = auto()
    DOUBLE_PLAY = auto()
    OUTFIELD_FLY = auto()
    SACRIFICE_FLY = auto()
    PRODUCTIVE_OUT = auto() # SHINRUI_DA
    INFIELD_HIT = auto()
    SINGLE = auto()
    DOUBLE = auto()
    TRIPLE = auto()
    HOME_RUN = auto()
    BALL_FOUR = auto()


# class Action:
#     @classmethod
#     def execute(cls, game):
#         cls.playing(game)
#         cls.next_phase().execute(game)

#     @staticmethod
#     def playing(game):
#         raise NotImplementedError()

#     @staticmethod
#     def next_action(game):
#         raise NotImplementedError()
        

class BatterSetAction:
    @staticmethod
    def play(game):
        pitcher = game.defense_player.pitcher
        pitcher.refresh()
        game.field.set_mound(pitcher)

        idx = game.next_batter_idx()
        batter = game.offense_player.nth_batter(idx)
        batter.refresh()
        # <-- find which batter box is prefered
        game.find.set_batter(batter, is_right=True)

        # <-- ask if position change / pinch hitter is needed

        return PrePitchAction.play(game)
        

class PrePitchAction:
    @staticmethod
    def play(game):
        # <-- set tactics card, use abilities, etc...
        return PitchAction.play(game)

    
class PitchAction:
    @staticmethod
    def play(game):
        # <-- set VS card to VSCardZone
        for player in game.players:
            player.open_vs_card()

        # <-- SP-Combo check
        # <-- Defense side => Offense side

        vs_off = game.offense_player.vs_card
        vs_def = game.defense_player.vs_card

        if isinstance(vs_off, VSCard) and isinstance(vs_def, VSCard):
            # <-- Point-Draw
            return PostPitchAction.play(game)
        else:
            return PostGaugeCheckAction.non_vs_play(game)


class PostPitchAction:
    @staticmethod
    def play(game):
        vs_off = game.offense_player.vs_card
        vs_def = game.defense_player.vs_card
        # <-- open reversed cards, use abilities, etc...
        return GaugeCheckAction.play(game)

    
class GaugeCheckAction:
    @staticmethod
    def play(game):
        # <-- double-play, sacrifice fly...

        vs_off = game.offense_player.vs_card
        vs_def = game.defense_player.vs_card
        # <-- judge the result of at-bat
        result = None
        return PostGaugeCheckAction.play(game, result)

    
class PostGaugeCheckAction:
    @staticmethod
    def non_vs_play(game):
        vs_off = game.offense_player.vs_card
        vs_def = game.defense_player.vs_card
        
        if not isinstance(vs_def, VSCard):
            result = AtBatResult.BALL_FOUR
            return PostGaugeCheckAction.play(game, result)
        else:
            result = AtBatResult.STRIKE_OUT
            return PostGaugeCheckAction.play(game, result)
    
    @staticmethod
    def play(game, result):
        # <-- set tactics card, use abilities, etc...
        return FinishAtBatAction.play(game, result)

    
class FinishAtBatAction:
    @staticmethod
    def play(game, result):
        # <-- move runners and so on
        # <-- refresh check
        if game.out_count >= 3:
            return FinishTopBottomInningPhase.play(game)

    @staticmethod
    def strike_out(game):
        game.out += 1

    @staticmethod
    def infield_grounder(game):
        pass

    @staticmethod
    def double_play(game):
        pass

    @staticmethod
    def outfield_fly(game):
        game.out += 1

    @staticmethod
    def sacrifice_fly(game):
        game.out += 1
        if game.out < 3:
            third_runner = game.field.runners[2]
            if third_runner is not None:
                game.add_score(1)
                game.field.runners[2] = None
                
    @staticmethod
    def productive_out(game):
        game.out += 1
        if game.out < 3:
            if game.field.runners[2] is not None:
                game.add_score(1)
            game.field.runners = [None] + game.field.runners[0:2]

    @staticmethod
    def infield_hit(game):
        if game.field.runners[2] is not None:
            game.add_score(1)
        batter = game.field.batter
        game.field.runners = [batter] + game.field.runners[0:2]

    @staticmethod
    def single(game):
        pass

    @staticmethod
    def double(game):
        num_returns = sum(
            runner is not None
            for runner in game.field.runners[1:3]
        )
        game.add_score(num_returns)
        batter = game.field.batter
        game.field.runners = [None, batter] + game.field.runners[0]

    @staticmethod
    def triple(game):
        num_returns = sum(
            runner is not None
            for runner in game.field.runners
        )
        game.add_score(num_returns)
        batter = game.field.batter
        game.field.runners = [None, None, batter]

    @staticmethod
    def home_run(game):
        num_returns = sum(
            runner is not None
            for runner in game.field.runners
        ) + 1
        game.add_score(num_returns)
        game.field.runners = [None, None, None]

    @staticmethod
    def ball_four(game):
        batter = game.field.batter
        runners = game.field.runners
        if None in runners: # not full-base
            runners.remove(None)
            game.field.runners = [batter] + runners
        else: # full-base
            game.field.runners = [batter] + runners[:-1]
            game.add_score(1)
