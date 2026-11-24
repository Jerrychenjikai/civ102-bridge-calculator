# all numbers in mm

class LineSegment:
    def __init__(self, axis: bool, value: float):
        # assume either vertical or horizontal
        self.axis: bool = axis # 0 for vertical line, i.e. value is for x axis, 1 for horizontal line, i.e. y axis
        self.value: float = value

class Rectangle:
    def __init__(self, x_range: tuple[float, float], y_range: tuple[float, float]):
        # assume all lines either vertical or horizontal
        self.ranges = (x_range, y_range)

    def is_touch(self, rect: Rectangle) -> bool:
        # TODO: check if overlap on other dimension as well
        # checks if the two rectangles share a side
        if self.ranges[0][0] == rect.ranges[0][1] \
            or self.ranges[0][1] == rect.ranges[0][0] \
            or self.ranges[1][0] == rect.ranges[1][1] \
            or self.ranges[1][1] == rect.ranges[1][0]:

            return True

        return False

    def center(self) -> tuple[float, float]:
        return (sum(self.ranges[0])/2, sum(self.ranges[1])/2)

    def area(self) -> float:
        return abs(self.ranges[0][0] - self.ranges[0][1]) \
            * abs(self.ranges[1][0] - self.ranges[1][1])

    def lower_bound(self) -> float:
        return min(self.ranges[1])

    def upper_bound(self) -> float:
        return max(self.ranges[1])

    def dimension(self) -> tuple[float, float]:
        return (abs(self.ranges[0][0] - self.ranges[0][1]), abs(self.ranges[1][0] - self.ranges[1][1]))

class CrossSection:
    def __init__(self):
        self.matboards: list[Rectangle] = []

        self.clear()

    def clear(self):
        self.resolved = False

        self.I: float = -1
        self.y_bar: float = -1
        self.lower_y: float = -1
        self.upper_y: float = -1
        self.total_area: float = -1


    def add_rectangle(self, rect: Rectangle):
        self.matboards.append(rect)
        self.clear()

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

    
    