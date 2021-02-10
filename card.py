from enum import Enum, Flag, auto
from . team_status import Position

class Course(Enum):
    CENTER = auto()
    HIGH = auto()
    LOW = auto()
    LEFT = auto()
    RIGHT = auto()


class MeetShotPoint(Enum):
    NULL = (auto(), "○")
    FILL = (auto(), "●")
    STAR = (auto(), "★")

    def __init__(self, id, icon):
        self.id = id
        self.icon = icon

    def __str__(self):
        return self.icon


class MeetShotPts(dict):
    def __init__(self):
        super().__init__(
            {
                course: MeetShotPoint.NULL
                for course in Course
            }
        )

    def __str__(self):
        lines = (
            "　{}　".format(self[Course.HIGH]),
            "{}{}{}".format(
                self[Course.LEFT],
                self[Course.CENTER],
                self[Course.RIGHT],
            ),
            "　{}　".format(self[Course.LOW]),
        )
        return "\n".join(lines)

    def clear(self, course):
        self[course] = MeetShotPoint.NULL

    def clear_all(self):
        for course in Course:
            self[course] = MeetShotPoint.NULL
        
    def replace_pts(self, from_point, to_point):
        """
        replace all 'from_point' included in self
        to 'to_point'
        """
        for course_point in self.items():
            if course_point[1] == from_point:
                self[course_point[0]] = to_point


class Card:
    def __init__(self, id):
        self.id = id


class PlayerCard(Card):    
    def __init__(self, id, bat_hand, player_type,
                 ms_pts, power, draw):
        super().__init__(id)
        self.bat_hand = bat_hand
        self.type = player_type
        self.ms_pts = ms_pts # meet/shot points
        self.power = power
        self.draw = draw
        self.ability = []

    def is_defensible(self, position):
        if position == Position.DH:
            return True
        if position == Position.PITCHER:
            return (
                self.Type.STARTER in self.type
                or
                self.Type.RELIEVER in self.type
            )
        if position == Position.CATCHER:
            return self.Type.CATCHER in self.type
        if position == Position.INFIELDER:
            return self.Type.INFIELDER in self.type
        if position == Position.OUTFIELDER:
            return self.Type.OUTFIELDER in self.type
        
    class Type(Flag):
        STARTER = auto()
        RELIEVER = auto()
        PITCHER = STARTER | RELIEVER
        CATCHER = auto()
        INFIELDER = auto()
        OUTFIELDER = auto()
        FIELDER = CATCHER | INFIELDER | OUTFIELDER
        UTIL_CI = CATCHER | INFIELDER
        UTIL_CO = CATCHER | OUTFIELDER
        UTIL_IO = INFIELDER | OUTFIELDER
        UTIL_CIO = CATCHER | INFIELDER | OUTFIELDER

    class BatHand(Flag):
        RIGHT = auto()
        LEFT = auto()
        SWITCH = RIGHT | LEFT
        
        
class TacticsCard(Card):
    def __init__(id, cost, tactics_type, effect):
        super().__init__(id)
        self.cost = cost
        self.type = tactics_type

    class Type(Flag):
        OFFENSE = auto()
        DEFENSE = auto()
        UTILITY = OFFENSE | DEFENSE
        

class VSCard(Card):
    def __init__(self, id, course, pw_off, pw_def):
        super().__init__(id)
        self.course = course
        self.pw_off = pw_off
        self.pw_def = pw_def
