from cross_section import *
import warnings

# all lengths in mm
# E in mPa
# force in kN
# moment in Nm
# force upward positive
# moment counterclockwise positive

class Force:
    def __init__(self, mag: float, pos: float):
        self.mag: float = mag # positive upward, negative downward
        self.pos: float = pos

class Diagram:
    def __init__(self, x_values: list[float]):
        if len(x_values) == 0:
            raise ValueError("x values cannot be empty")
        
        self.x_values: list[float] = x_values
        self.y_values: list[float] = []

    def update_y_values(self, y: list[float]):
        if len(y) != len(self.x_values):
            raise ValueError("len of y and x must match")
        
        self.y_values = y
    

class Beam:
    def __init__(self, length: int, E: int):
        self.cross_section: CrossSection = CrossSection()
        self.length: int = length #coordinate 0 ~ length, inclusive
        self.forces: list[Force] = []
        self.E: int = E

        self.simulation_list = range(0, self.length+1)

        self.clear()

    def clear(self):
        self.shear: Diagram = Diagram(self.simulation_list)
        self.moment: Diagram = Diagram(self.simulation_list) #counterclockwise positive
        self.phi: Diagram = Diagram(self.simulation_list)
        self.top_tensile: Diagram = Diagram(self.simulation_list)
        self.bottom_tensile: Diagram = Diagram(self.simulation_list)
        self.y_bar_shear: Diagram = Diagram(self.simulation_list)

        self.glue_shears: list[Diagram] = []
        for i in self.cross_section.horizontal_glue_joints:
            self.glue_shears.append(Diagram(self.simulation_list))

        self.reaction_force_left: Force = Force(0, 0)
        self.reaction_force_right: Force = Force(0, self.length)
        
        self.solved = False

    def add_force(self, force: Force):
        if not within(0, self.length, force.pos):
            warnings.warn("Force outside the range of beam")
            return
        
        self.forces.append(force)

        self.clear()

    def remove_force(self, force: Force):
        self.forces.remove(force)

        self.clear()

    def clear_force(self):
        self.forces = []

        self.clear()

    def solve_reaction_forces(self):
        # 0. solve for reaction forces
        total_moment = 0 # relative to pos = 0
        total_shear = 0

        for i in self.forces:
            total_moment += i.pos * i.mag
            total_shear += i.mag

        self.reaction_force_right.mag = -(total_moment)/self.length
        self.reaction_force_left.mag = -(total_shear + self.reaction_force_right.mag)

    def solve(self):
        self.solve_reaction_forces()
        self.cross_section.solve()
        forces = self.forces + [self.reaction_force_left, self.reaction_force_right]

        # 1. draw shear force diagram
        y_values = []

        for i in self.simulation_list:
            shear_summ = 0
            for j in forces:
                if j.pos <= i:
                    shear_summ += j.mag

            y_values.append(shear_summ)

        self.shear.update_y_values(y_values)

        # 2. draw bending moment diagram
        y_values = []
        for i in self.simulation_list:
            moment_summ = 0

            for j in forces:
                if j.pos < i:
                    moment_summ -= (i - j.pos) * (j.mag) # minus to align with sign conventions
            y_values.append(moment_summ)

        self.moment.update_y_values(y_values)

        # 3. draw phi diagram
        # assume constant Cross Section throughout
        y_values = [m / (self.E * self.cross_section.I) for m in self.moment.y_values]

        self.phi.update_y_values(y_values)

        # 4. draw top tensile diagram
        y_values = [m * (self.cross_section.upper_y - self.cross_section.y_bar) / self.cross_section.I * 1000 for m in self.moment.y_values]

        self.top_tensile.update_y_values(y_values)

        # 5. draw bottom tensile diagram
        y_values = [m * (self.cross_section.lower_y - self.cross_section.y_bar) / self.cross_section.I * 1000 for m in self.moment.y_values]
        
        self.bottom_tensile.update_y_values(y_values)

        # 6. draw shear tension at glue joints:
        for i in range(len(self.cross_section.horizontal_glue_joints)):
            y = self.cross_section.horizontal_glue_joints[i]
            width = self.cross_section.glue_width_at_height(y)
            Q = self.cross_section.Q_at_height(y)
            I = self.cross_section.I
            y_values = [V * Q / I /width * 1000 for V in self.shear.y_values] # multiply by 1000 to align with unit convention

            self.glue_shears[i].update_y_values(y_values)

        # 7. calculate shear at y_bar
        y = self.cross_section.y_bar
        Q = self.cross_section.Q_at_height(y)
        I = self.cross_section.I
        width = self.cross_section.glue_width_at_height(y)
        y_values = [V * Q / I /width * 1000 for V in self.shear.y_values]

        self.y_bar_shear.update_y_values(y_values)


    
    