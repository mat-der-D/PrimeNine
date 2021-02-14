from copy import deepcopy
import numpy as np
from . card import Course, Point, Card, PlayerCard, TacticsCard, VSCard


class Rule:
    def __init__(self, max_inning, max_extra_inning, is_dh):
        self.max_inning = max_inning
        self.max_extra_inning = max_extra_inning
        self.id_dh = is_dh


class ScoreBoard:
    def __init__(self):
        self.board = [[], []] # top, bottom

    def new_inning(self, game):
        self.board[game.is_bottom].append(None)

    @property
    def total_score(self):
        total_score = [
            sum(filter(None, each_score))
            for each_score in self.board
        ]
        return total_score

    def add_score(self, game, n):
        board = self.board[game.is_bottom]
        if board[-1] is None:
            board[-1] = n
        else:
            board[-1] += n

    def fill_zero(self, game):
        self.add_score(game, 0)

    @property
    def winning_team(self):
        total_score = self.total_score
        if total_score[0] == total_score[1]:
            return None
        else:
            return np.argmax(total_score)


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
        

class Gauge:
    def __init__(self, default: dict):
        self._default = default
        self.gauge = self._default

    def __str__(self):
        return self.gauge.__str__()

    def __repr__(self):
        return self.gauge.__repr__()

    def __getitem__(self, key):
        return self.gauge.__getitem__(key)

    def __setitem__(self, key, value):
        if key not in self.gauge:
            raise KeyError(key)
        self.gauge[key] = value
        
    def refresh(self):
        self.gauge = self._default


class HitGauge(Gauge):
    def __init__(self):
        default = {
            4: HomeRun,
            3: Triple,
            2: Double,
            1: Single,
            0: Single,
            -1: InfieldHit,
            -2: InfieldGrounder,
        }
        super().__init__(default)

    def __getitem__(self, power_diff):
        if not isinstance(power_diff, int):
            raise KeyError(power_diff)
        if power_diff > 4:
            return super().__getitem__(4)
        elif power_diff < -2:
            return super().__getitem__(-2)
        else:
            return super().__getitem__(power_diff)

        
class OutGage(Gauge):
    def __init__(self):
        default = {
            Course.HIGH: OutfieldFly,
            Course.LEFT: StrikeOut,
            Course.CENTER: StrikeOut,
            Course.RIGHT: StrikeOut,
            Course.LOW: InfieldGrounder,
        }
        super().__init__(default)
        

# **************
# * Main Class *
# **************
class Game:
    def __init__(self, visitor_player, home_player, rule):

        self.score_board = ScoreBoard()
        self.out = None
        self.is_bottom = None # top:0, bottom:1
        self.inning = None
        self.next_batter = [None, None]

        self.players = [visitor_player, home_player]
        self.field = Field()

        self.hit_gauge = HitGauge()
        self.out_gauge = OutGauge()
        
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
    @property
    def is_final_inning(self):
        return game.inning >= self.RULE.max_inning

    @property
    def can_extend(self):
        return game.inning < self.RULE.max_extra_inning

    def increment_pitch_inning(self):
        def_player = self.players[not self.is_bottom]
        def_player.increment_pitch_inning()
    
    # --- score board ---
    def extend_score_board(self):
        self.score_board.new_inning(self)

    def add_score(self, n):
        self.score_board.add_score(self, n)

    def fill_zero_score(self):
        self.score_board.fill_zero(self)

    @property
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


class Change(Exception):
    """
    raise Change at the time of three-out-change
    """
    pass


# **********
# * Phases *
# **********
class Phase:
    @classmethod
    def execute(cls, game):
        cls.playing(game)
        cls.next_phase(game).execute(game)

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
        # <-- refresh all cards (including both team and deck)
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
        try:
            BatterSetAction.execute(game, None)
        except Change:
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
            if game.is_final_inning and game.winning_team == 1:
                raise GameSet()
            game.is_bottom = True
            return StartTopBottomInningPhase


class FinishInningPhase(Phase):
    @staticmethod
    def playing(game):
        # <-- check tactics card
        pass

    @staticmethod
    def next_phase(game):
        if not game.is_final_inning:
            return StartInningPhase
        elif game.winning_team is not None:
            raise GameSet()
        elif game.can_extend:
            return StartInningPhase
        else:
            raise GameSet()
        
        
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
class Action:
    @classmethod
    def execute(cls, game, result):
        result = cls.playing(game, result)
        cls.next_action(game).execute(game, result)

    @staticmethod
    def playing(game, result):
        raise NotImplementedError()

    @staticmethod
    def next_action(game):
        raise NotImplementedError()
        

class BatterSetAction(Action):
    @staticmethod
    def playing(game, result):
        pitcher = game.defense_player.pitcher
        pitcher.refresh()
        game.field.set_mound(pitcher)

        idx = game.next_batter_idx()
        batter = game.offense_player.nth_batter(idx)
        batter.refresh()
        # <-- find which batter box is prefered
        game.find.set_batter(batter, is_right=True)

        # <-- ask if position change / pinch hitter is needed

        return None
    
    @staticmethod
    def next_action(game):
        return PrePitchAction
        

class PrePitchAction(Action):
    @staticmethod
    def playing(game, result):
        # <-- set tactics card, use abilities, etc...
        return None

    @staticmethod
    def next_action(game):
        return PitchAction

class PitchAction(Action):
    @staticmethod
    def playing(game, result):
        # <-- set VSCard to VSCardZone
        for player in game.players:
            player.open_vs_card()

        # <-- SPCombo Check
        # <-- Defense side => Offense side

        return None

    @staticmethod
    def next_action(game):
        vs_off = game.offense_player.vs_card
        vs_def = game.defense_player.vs_card
        if isinstance(vs_off, VSCard) and isinstance(vs_def, VSCard):
            # <-- Point-Draw
            return PostPitchAction
        else:
            return GaugeCheckAction


class PostPitchAction(Action):
    @staticmethod
    def playing(game, result):
        vs_off = game.offense_player.vs_card
        vs_def = game.defense_player.vs_card
        # <-- open reversed cards, use abilities, etc...
        # <-- double-play, sacrifice fly...
        return None

    @staticmethod
    def next_action(game):
        return GaugeCheckAction

        
class GaugeCheckAction(Action):
    @staticmethod
    def playing(game, result):
        vs_off = game.offense_player.vs_card
        vs_def = game.defense_player.vs_card
        if not isinstance(vs_def, VSCard):
            return BallFour
        elif not isinstance(vs_off, VSCard):
            return StrikeOut
        elif GaugeCheckAction.is_just_meet(game, vs_off, vs_def):
            return GaugeCheckAction.hit_gauge_playing(game, vs_off, vs_def)
        else:
            return GaugeCheckAction.out_gauge_playing(game, vs_def)

    @staticmethod
    def is_just_meet(game, vs_off, vs_def):
        if vs_def.course == vs_off.course:
            return True
        meet_pt = game.field.batter.ms_pts[vs_def.course]
        shot_pt = game.field.mound.ms_pts[vs_def.course]
        if meet_pt == Point.STAR:
            return True
        elif meet_pt == Point.FILL and shot_pt != Point.STAR:
            return True
        else:
            return False
        
    @staticmethod
    def hit_gauge_playing(game, vs_off, vs_def):
        offense_power = game.field.batter.power + vs_off.pw_off
        defense_power = game.field.mound.power + vs_def.pw_def
        return game.hit_gauge[offense_power - defense_power]

    @staticmethod
    def out_gauge_playing(game, vs_def):
        return game.out_gauge[vs_def.course]
    
    @staticmethod
    def next_action(game):
        return PostGaugeCheckAction


class PostGaugeCheckAction(Action):
    @staticmethod
    def playing(game, result):
        # <-- set tactics card, use abilities, etc...
        return result

    @staticmethod
    def next_action(game):
        return FinishAtBatAction


class FinishAtBatAction(Action):
    @staticmethod
    def playing(game, result):
        result.apply(game)
        if game.is_final_inning and game.winning_team == 1:
            raise GameSet()
        # <-- refresh all cards (with few exceptions)
        return None
    
    @staticmethod
    def next_action(game):
        if game.out >= 3:
            raise Change()
        return BatterSetAction


# ******************
# * At-Bat Results *
# ******************
class AtBatResult:
    @staticmethod
    def apply(game):
        pass


class StrikeOut(AtBatResult):
    @staticmethod
    def apply(game):
        game.out += 1


class InfieldGrounder(AtBatResult):
    @staticmethod
    def apply(game):
        # <--- select which runner be out
        pass


class DoublePlay(AtBatResult):
    @staticmethod
    def apply(game):
        # <--- select which runner be out
        pass


class OutfieldFly(AtBatResult):
    @staticmethod
    def apply(game):
        game.out += 1


class SacrificeFly(AtBatResult):
    @staticmethod
    def apply(game):
        game.out += 1
        if game.out < 3:
            third_runner = game.field.runners[2]
            if third_runner is not None:
                game.add_score(1)
                game.field.runners[2] = None
    

class ProductiveOut(AtBatResult):
    @staticmethod
    def apply(game):
        game.out += 1
        if game.out < 3:
            if game.field.runners[2] is not None:
                game.add_score(1)
            game.field.runners = [None] + game.field.runners[:-1]
        

class InfieldHit(AtBatResult):
    @staticmethod
    def apply(game):
        if game.field.runners[2] is not None:
            game.add_score(1)
            batter = game.field.batter
            game.field.runners = [batter] + game.field.runners[:-1]


class Single(AtBatResult):
    @staticmethod
    def apply(game):
        # <-- swift runner check
        pass


class Double(AtBatResult):
    @staticmethod
    def apply(game):
        num_returns = sum(
            runner is not None
            for runner in game.field.runners[1:]
        )
        game.add_score(num_returns)
        batter = game.field.batter
        game.field.runners = [None, batter] + game.field.runners[0]


class Triple(AtBatResult):
    @staticmethod
    def apply(game):
        num_returns = sum(
            runner is not None
            for runner in game.field.runners
        )
        game.add_score(num_returns)
        batter = game.field.batter
        game.field.runners = [None, None, batter]


class HomeRun(AtBatResult):
    @staticmethod
    def apply(game):
        num_returns = sum(
            runner is not None
            for runner in game.field.runners
        ) + 1
        game.add_score(num_returns)
        game.field.runners = [None, None, None]


class BallFour(AtBatResult):
    @staticmethod
    def apply(game):
        batter = game.field.batter
        runners = game.field.runners
        if None in runners: # not full-base
            runners.remove(None)
            game.field.runners = [batter] + runners
        else: # full-base
            game.field.runners = [batter] + runners[:-1]
            game.add_score(1)
