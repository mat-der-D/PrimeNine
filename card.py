from enum import Enum, Flag, auto


class BatHand(Flag):
    RIGHT = auto()
    LEFT = auto()
    SWITCH = RIGHT | LEFT


class Position(Enum):
    STARTER = auto()
    RELIEVER = auto()
    PITCHER = STARTER & RELIEVER
    CATCHER = auto()
    INFIELDER = auto()
    OUTFIELDER = auto()
    UTIL_CI = CATCHER | INFIELDER
    UTIL_CO = CATCHER | OUTFIELDER
    UTIL_IO = CATCHER | OUTFIELDER
    UTIL_CIO = CATCHER | INFIELDER | OUTFIELDER
    DH = auto()


class Course(Enum):
    CENTER = auto()
    HIGH = auto()
    LOW = auto()
    LEFT = auto()
    RIGHT = auto()


class Point(Enum):
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
                course: Point.NULL
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
        self[course] = Point.NULL

    def clear_all(self):
        for course in Course:
            self[course] = Point.NULL
        
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

    def refresh(self):
        pass


class PlayerCard(Card):    
    def __init__(self, id, bat_hand, position,
                 ms_pts, power, draw):
        super().__init__(id)
        self.bat_hand = bat_hand
        self.position = position

        # --- default ---
        self._ms_pts = ms_pts # meet/shot points
        self._power = power
        self._draw = draw
        self.refresh()
        self.ability = []

    def refresh(self):
        self.ms_pts = self._ms_pts
        self.power = self._power
        self.draw = self._draw
        
    def is_defensible(self, position):
        if position == Position.DH:
            return True
        else:
            return position in self.position
        
        
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
        self._course = course
        self.course = self._course
        self.pw_off = pw_off
        self.pw_def = pw_def

    def refresh(self):
        self.course = self._course
