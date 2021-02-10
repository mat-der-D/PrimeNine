from enum import Enum, auto
import pandas as pd


class Position(Enum):
    PITCHER = auto()
    CATCHER = auto()
    INFIELDER = auto()
    OUTFIELDER = auto()
    DH = auto()


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
