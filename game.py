from copy import deepcopy
from . card import Card, PlayerCard, TacticsCard, VSCard


class Game:
    def __init__(self, deck_masters, teams,
                 max_inning, max_extra_inning, is_dh):
        self.scores = [0, 0]
        self.out_count = 0
        self.is_bottom = False # top/bottom === OMOTE/URA
        self.inning = 0
        self.next_batter = [0, 0]
        self.deck_masters = deck_masters # (DeckMaster, DeckMaster)
        self.teams = teams # (TeamStatus, TeamStatus)

        self.field = Field()

        # --- game rules ---
        self.MAX_INNING = max_inning
        self.MAX_EXTRA_INNING = max_extra_inning
        self.IS_DH = is_dh

    def next_batter_idx(self):
        next_idx = self.next_batter[self.is_bottom]
        self.next_batter[self.is_bottom] \
            = (next_idx + 1) % 9
        return next_idx
        
    def playball_and_return_winner(self):
        return StartGamePhase.playball(self)


# **********
# * Phases *
# **********
class StartGamePhase:
    @staticmethod
    def playball(game):
        for master in game.deck_masters:
            master.draw_n(5)
        return StartInningPhase.next_inning(game)


class StartInningPhase:
    @staticmethod
    def next_inning(game):
        game.inning += 1
        game.is_bottom = False
        return StartTopBottomInningPhase.play(game)
    
    
class StartTopBottomInningPhase:
    @staticmethod
    def play(game):
        # <-- position validation (in case of pinch hitter)
        # <-- change players or positions if needed
        return AtBatPhase.play(game)
    
    
class AtBatPhase:
    """
    Detailed processes are implemented in **Action classes
    """
    @staticmethod
    def play(game):
        return BatterSetAction.play(game)
    

class FinishTopBottomInningPhase:
    @staticmethod
    def play(game):
        game.out_count = 0
        game.field.runners = [None, None, None]
        # <-- discard hands (not implemented yet)
        game.teams[not game.is_bottom].pitch_innings += 1
        if game.is_bottom:
            return FinishInningPhase.judge_game_set(game)
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


class BatterSetAction:
    @staticmethod
    def play(game):
        pitcher = game.teams[not game.is_bottom].pitcher
        game.field.take_mound(pitcher)

        idx = game.next_batter_idx()
        batter = game.teams[game.is_bottom].nth_batter(idx)
        # <-- find which batter box is prefered
        game.field.step_into_batter_box(batter, is_right=True)

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
        for play_zone in game.field.play_zones:
            play_zone.open_all()

        # <-- SP-Combo check
        # <-- Defense side => Offense side
        
        vs_off = game.field.play_zones[game.is_bottom][0][0]
        vs_def = game.field.play_zones[not game.is_bottom][0][0]

        if isinstance(vs_off, VSCard) and isinstance(vs_def, VSCard):
            # <-- Point-Draw
            return PostPitchAction.play(game)
        else:
            return PostGaugeCheckAction.non_vs_play(game)


class PostPitchAction:
    @staticmethod
    def play(game):
        vs_off = game.field.play_zones[game.is_bottom][0][0]
        vs_def = game.field.play_zones[not game.is_bottom][0][0]
        # <-- open reversed cards, use abilities, etc...
        return GaugeCheckAction.play(game)

    
class GaugeCheckAction:
    @staticmethod
    def play(game):
        # <-- double-play, sacrifice fly...
        
        vs_off = game.field.play_zones[game.is_bottom][0][0]
        vs_def = game.field.play_zones[not game.is_bottom][0][0]
        # <-- judge the result of at-bat
        result = None
        return PostGaugeCheckAction.play(game, result)

    
class PostGaugeCheckAction:
    @staticmethod
    def non_vs_play(game):
        vs_off = game.field.play_zones[game.is_bottom][0][0]
        vs_def = game.field.play_zones[not game.is_bottom][0][0]
        
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
        if game.out_count >= 3:
            return FinishTopBottomInningPhase.play(game)

    @staticmethod
    def strike_out(game):
        game.out_count += 1

    @staticmethod
    def infield_grounder(game):
        pass

    @staticmethod
    def double_play(game):
        pass

    @staticmethod
    def outfield_fly(game):
        game.out_count += 1

    @staticmethod
    def sacrifice_fly(game):
        game.out_count += 1
        if game.out_count < 3:
            third_runner = game.field.runners[2]
            if third_runner is not None:
                game.score[game.is_bottom] += 1
                game.field.runners[2] = None
                
    @staticmethod
    def productive_out(game):
        game.out_count += 1
        if game.out_count < 3:
            if game.field.runners[2] is not None:
                game.score[game.is_bottom] += 1
            game.field.runners = [None] + game.field.runners[0:2]

    @staticmethod
    def infield_hit(game):
        if game.field.runners[2] is not None:
            game.score[game.is_bottom] += 1
        batter = game.field.batter_box[0]
        game.field.runners = [batter] + game.field.runners[0:2]

    @staticmethod
    def single(game):
        pass

    @staticmethod
    def double(game):
        added_score = sum(
            runner is not None
            for runner in game.field.runners[1:3]
        )
        game.scores[game.is_bottom] += added_score
        batter = game.field.batter_box[0]
        game.field.runners = [None, batter] + game.field.runners[0]

    @staticmethod
    def triple(game):
        added_score = sum(
            runner is not None
            for runner in game.field.runners
        )
        game.scores[game.is_bottom] += added_score
        batter = game.field.batter_box[0]
        game.field.runners = [None, None, batter]

    @staticmethod
    def home_run(game):
        added_score = sum(
            runner is not None
            for runner in game.field.runners
        ) + 1
        game.scores[game.is_bottom] += added_score
        game.field.runners = [None, None, None]

    @staticmethod
    def ball_four(game):
        batter = game.field.batter_box[0]
        runners = game.field.runners
        if None in runners: # not full-base
            runners.remove(None)
            game.field.runners = [batter] + runners
        else: # full-base
            game.field.runners = [batter] + runners[:-1]
            game.score[game.is_bottom] += 1
