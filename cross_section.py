# all numbers in mm
# assume: no overlap between Rectangles

from constants import *

def within(upper, lower, value):
    return max(upper, lower) >= value >= min(upper, lower)

def range_len(range: tuple[float, float]) -> float:
    return abs(range[0]-range[1])

class Rectangle:
    def __init__(self, x_range: tuple[float, float], y_range: tuple[float, float]):
        # assume all lines either vertical or horizontal
        self.update_ranges(x_range, y_range)

    def update_data(self):
        # 0 means x axis, 1 means y axis
        self.longer_axis: bool = 0 if range_len(self.ranges[0]) > range_len(self.ranges[1]) else 1
        self.shorter_axis: bool = 1 - self.longer_axis

        self.thickness: float = range_len(self.ranges[self.shorter_axis])
        self.width: float = range_len(self.ranges[self.longer_axis])
        
        # places where board is touched on longer axis
        self.touches: list[float] = []

    def update_ranges(self, x_range: tuple[float, float], y_range: tuple[float, float]):
        # assume all lines either vertical or horizontal
        self.ranges = (x_range, y_range)

        self.update_data()

    
    def is_touch(self, rect: Rectangle) -> tuple[bool, float, float]: # touched, pos of touch, length of touch
        # checks if the two rectangles share a side
        if (eq(self.left_bound(), rect.right_bound()) \
            or eq(self.right_bound(), rect.left_bound())) \
            and (self.upper_bound() > rect.lower_bound() \
                 and self.lower_bound() < rect.upper_bound()):

            POI = [0,0]
            POI[0] = self.left_bound() if eq(self.left_bound(), rect.right_bound()) else self.right_bound()
            up = min(self.upper_bound(), rect.upper_bound())
            down = max(self.lower_bound(), rect.lower_bound())
            POI[1] = (up + down)/2

            return True, POI[self.longer_axis], (up - down)

        if (eq(self.upper_bound(), rect.lower_bound()) \
            or eq(self.lower_bound(), rect.upper_bound())) \
            and (self.right_bound() > rect.left_bound() \
                 and self.left_bound() < rect.right_bound()):

            POI = [0,0]
            POI[1] = self.upper_bound() if eq(self.upper_bound(), rect.lower_bound()) else self.lower_bound()
            right = min(self.right_bound(), rect.right_bound())
            left = max(self.left_bound(), rect.left_bound())
            POI[0] = (left + right)/2

            return True, POI[self.longer_axis], (right - left)
        return False, -1, 0

    def calculate_buckle_strength(self, y_bar: float, E: int = ELASTIC_MODULUS, poisson: float = POISSON):
        def buckling_formula(k: float, width: float, E: int = E, poisson: float = poisson):
            return k * (PI**2) * E /(12 * (1-poisson**2)) * ((self.thickness/width)**2)
        
        self.touches.sort()

        min_compression_limit = float('inf')

        if len(self.touches) == 0:
            #manipulation of Euler's formula for stress
            return (PI**2)*E*(self.thickness**2)/(BRIDGE_LENGTH**2)/12

        lower_bound = self.lower_bound() if self.longer_axis == 1 else self.left_bound()
        upper_bound = self.upper_bound() if self.longer_axis == 1 else self.right_bound()

        if not eq(self.touches[0], lower_bound):
            min_compression_limit = min(min_compression_limit, buckling_formula(0.425, abs(self.touches[0] - lower_bound)))

        if not eq(self.touches[-1], upper_bound):
            min_compression_limit = min(min_compression_limit, buckling_formula(0.425, abs(self.touches[-1] - upper_bound)))

        for i in range(len(self.touches)-1):
            if eq(self.touches[i], self.touches[i+1]):
                continue

            if self.longer_axis == 0:
                min_compression_limit = min(min_compression_limit, buckling_formula(4, abs(self.touches[i] - self.touches[i+1])))
            elif max(self.touches[i], self.touches[i+1]) > y_bar:
                min_compression_limit = min(min_compression_limit, buckling_formula(6, abs(max(self.touches[i], y_bar) - max(self.touches[i+1], y_bar))))
            # if hotizontal then constant pressure, hence use k = 4
            # if vertical then linearly varying pressure, hence use k = 6
            # professor did not give formula for linearly varying pressure on boards with 3 restrained sides, hence neglect those
            # for vertical matboards, only account for the part under compression i.e. above y_bar, hence the max y_bar stuff

        return min_compression_limit

    def center(self) -> tuple[float, float]:
        return (sum(self.ranges[0])/2, sum(self.ranges[1])/2)

    def area(self) -> float:
        return abs(self.ranges[0][0] - self.ranges[0][1]) \
            * abs(self.ranges[1][0] - self.ranges[1][1])

    def lower_bound(self) -> float:
        return min(self.ranges[1])

    def upper_bound(self) -> float:
        return max(self.ranges[1])

    def right_bound(self) -> float:
        return max(self.ranges[0])

    def left_bound(self) -> float:
        return min(self.ranges[0])

    def dimension(self) -> tuple[float, float]:
        return (abs(self.ranges[0][0] - self.ranges[0][1]), abs(self.ranges[1][0] - self.ranges[1][1]))

    def at_height(self, y: float) -> bool: 
        # see if the rectangle exists at certain height
        return within(self.ranges[1][0], self.ranges[1][1], y)

    def cross_height(self, y: float) -> bool:
        return self.at_height(y) and not eq(self.ranges[1][0], y) and not eq(self.ranges[1][1], y)

class CrossSection:
    def __init__(self):
        self.clear_rect()
        self.clear()

    def clear(self):
        self.resolved: bool = False

        self.I: float = -1
        self.y_bar: float = -1
        self.lower_y: float = -1
        self.upper_y: float = -1
        self.total_area: float = -1

    def clear_rect(self):
        self.matboards: list[Rectangle] = []
        self.horizontal_glue_joints: list[float] = []

        self.clear()

    def add_rect(self, rect: Rectangle):
        self.matboards.append(rect)
        self.clear()

    def add_glue(self, y:float):
        if eq(self.glue_width_at_height(y), 0):
            raise ValueError("does not have any surface to glue on")
        self.horizontal_glue_joints.append(y)

    def solve_touch(self):
        for i in self.matboards:
            i.update_data()
            for j in self.matboards:
                if i == j:
                    continue
                touched, pos, _ = i.is_touch(j)
                if touched:
                    i.touches.append(pos)

    def solve(self):
        if len(self.matboards) == 0:
            raise ValueError("The cross section has no area")
        
        # 0. basics
        self.lower_y = float('inf')
        self.upper_y = float('-inf')

        for i in self.matboards:
            self.lower_y = min(self.lower_y, i.lower_bound())
            self.upper_y = max(self.upper_y, i.upper_bound())

        # 1. resolve y bar
        self.total_area = 0
        total_first_moment_of_area = 0

        for i in self.matboards:
            self.total_area += i.area()
            total_first_moment_of_area += i.area() * i.center()[1]

        self.y_bar = total_first_moment_of_area / self.total_area

        # 2. resolve I
        self.I = 0

        for i in self.matboards:
            dimension = i.dimension()
            self.I += dimension[0] * (dimension[1] ** 3) / 12
            self.I += i.area() * ((i.center()[1] - self.y_bar) ** 2)

        self.resolved = True

    def glue_width_at_height(self, y: float) -> float:
        ans = 0

        up: list[Rectangle] = []
        down: list[Rectangle] = []

        for i in self.matboards:
            if i.cross_height(y):
                ans += i.dimension()[0]
            elif i.at_height(y):
                if i.center()[1] > y:
                    up.append(i)
                else:
                    down.append(i)

        for i in up:
            for j in down:
                _, _, length = i.is_touch(j)
                ans += length

        return ans

    def Q_at_height(self, y: float) -> float:
        # assume upper_y is free of shear
        if not self.resolved:
            self.solve()

        ans = 0

        for i in self.matboards:
            a = i
            if a.at_height(y):
                a = Rectangle(a.ranges[0], (max(a.ranges[1][0], y), max(a.ranges[1][1], y)))
            if a.lower_bound() >= y:
                ans += a.area() * (a.center()[1] - self.y_bar)

        return ans
                
            


    
    