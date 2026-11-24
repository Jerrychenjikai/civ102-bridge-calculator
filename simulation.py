import matplotlib.pyplot as plt
from beam import *
from cross_section import *
from constants import *

beam = Beam(BRIDGE_LENGTH, ELASTIC_MODULUS)

shear_max = Diagram(beam.simulation_list)
shear_min = Diagram(beam.simulation_list)
moment = Diagram(beam.simulation_list)
phi = Diagram(beam.simulation_list)
top_tensile = Diagram(beam.simulation_list)
bottom_tensile = Diagram(beam.simulation_list)
glue_shears: list[Diagram] = []
moment_constraints: list[float] = [] #moment constraints from local buckling of boards

train_len = 960
lightest_train_weight = 0.1 #kN

def generate_load(lightest_freight_weight: float):
    loads = []
    freight_weights = [lightest_freight_weight * 1.39 * 1.1, 
                       lightest_freight_weight,
                       lightest_freight_weight * 1.1]

    # assume locomotive at start, lightest in middle, heavier at end
    length = 0

    for weight in freight_weights:
        length += 52
        loads.append(Force(-weight/2, -length))
        length += 176
        loads.append(Force(-weight/2, -length))
        length += 164

    return loads

def move_loads(pos: float, loads: list[Force]):
    for i in loads:
        i.pos += pos

def elementwise_max(a: list[float], b: list[float]):
    if len(a) == 0:
        return b[:]
    if len(b) == 0:
        return a[:]
    if len(a) != len(b):
        raise ValueError("lists have to be same length")
    return [max(x, y) for x, y in zip(a, b)]

def elementwise_min(a: list[float], b: list[float]):
    if len(a) == 0:
        return b[:]
    if len(b) == 0:
        return a[:]
    if len(a) != len(b):
        raise ValueError("lists have to be same length")
    return [min(x, y) for x, y in zip(a, b)]

def max_abs_list(a: list[float], b: list[float]):
    if len(a) == 0:
        return b[:]
    if len(b) == 0:
        return a[:]
    if len(a) != len(b):
        raise ValueError("lists have to be same length")

    ans = []
    for i in range(len(a)):
        if abs(a[i]) > abs(b[i]):
            ans.append(a[i])
        else:
            ans.append(b[i])
    return ans

def run_train():
    global beam
    global shear_max, shear_min, phi, moment, train_len, top_tensile, bottom_tensile
    global glue_shears, moment_constraints
    global lightest_train_weight

    loads = generate_load(lightest_train_weight) # lightest train weighs 100N

    glue_shears = []
    for i in beam.cross_section.horizontal_glue_joints:
        glue_shears.append(Diagram(beam.simulation_list))

    for i in range(beam.length + train_len + 1):
        beam.clear_force()
        for j in loads:
            beam.add_force(j)

        beam.solve()

        shear_max.update_y_values(elementwise_max(beam.shear.y_values, shear_max.y_values))
        shear_min.update_y_values(elementwise_min(beam.shear.y_values, shear_min.y_values))
        moment.update_y_values(max_abs_list(beam.moment.y_values, moment.y_values))
        phi.update_y_values(max_abs_list(beam.phi.y_values, phi.y_values))
        top_tensile.update_y_values(max_abs_list(beam.top_tensile.y_values, top_tensile.y_values))
        bottom_tensile.update_y_values(max_abs_list(beam.bottom_tensile.y_values, bottom_tensile.y_values))

        for j in range(len(beam.cross_section.horizontal_glue_joints)):
            glue_shears[j].update_y_values(max_abs_list(beam.glue_shears[j].y_values, glue_shears[j].y_values))

        move_loads(1, loads)

    # calculate local buckling stress -> irrelevant to train load
    moment_constraints = []
    beam.cross_section.solve_touch()
    for i in beam.cross_section.matboards:
        stress_limit = i.calculate_buckle_strength()
        # stress = my/i
        y = (i.center()[1] - beam.cross_section.y_bar)
        if not eq(y, 0, tol = 1e-6):
            m_limit = - stress_limit * beam.cross_section.I / y / 1000
            moment_constraints.append(m_limit)

def parse_command(command: str):
    global shear_max, shear_min, moment, phi, top_tensile, bottom_tensile
    global glue_shears, moment_constraints
    global lightest_train_weight
    
    tokens = command.strip().split()
    if not tokens:
        return

    cmd = tokens[0].lower()
    args = tokens[1:]

    if cmd == "help":
        print("Command list: ")
        print("  help: show command list")
        print("  add_rect x1 x2 y1 y2: Add rectangle cross section (xmin xmax ymin ymax)")
        print("  clear_rect: clear all cross sections and glue tabs")
        print("  run: run train through and plot graphs")
        print("  change_weight w: change weight of lightest train")
        print("  add_glue y: add a glue joint at height y")

    elif cmd == "change_weight":
        w, = map(float, args)
        lightest_train_weight = w

    elif cmd == "add_glue":
        y, = map(float, args)
        beam.cross_section.add_glue(y)

    elif cmd == "add_rect":
        x1, x2, y1, y2 = map(float, args)
        rect = Rectangle((x1, x2), (y1, y2))
        beam.cross_section.add_rect(rect)

    elif cmd == "clear_rect":
        beam.cross_section.clear_rect()

    elif cmd == "run":
        beam.cross_section.solve()

        shear_max = Diagram(beam.simulation_list)
        shear_min = Diagram(beam.simulation_list)
        moment = Diagram(beam.simulation_list)
        phi = Diagram(beam.simulation_list)
        top_tensile = Diagram(beam.simulation_list)
        bottom_tensile = Diagram(beam.simulation_list)

        run_train()

        # 窗口 1: 内力与曲率响应图
        fig1, axs = plt.subplots(4, 1, figsize=(9, 10), sharex=True)

        # 1. 正向最大剪力图
        axs[0].plot(shear_max.x_values, shear_max.y_values, label="Max Shear Force (kN)", color="tab:blue")
        axs[0].set_ylabel("Max Shear (kN)")
        axs[0].grid(True)
        axs[0].legend()

        # 2. 负向最小剪力图
        axs[1].plot(shear_min.x_values, shear_min.y_values, label="Min Shear Force (kN)", color="tab:cyan")
        axs[1].set_ylabel("Min Shear (kN)")
        axs[1].grid(True)
        axs[1].legend()

        # 3. 弯矩图
        axs[2].plot(moment.x_values, moment.y_values, label="Bending Moment (Nm)", color="tab:orange")
        for i in moment_constraints:
            axs[2].axhline(y=i, color='red', linestyle='--', linewidth=1.5, label="moment limit from local buckling")
        axs[2].set_ylabel("Moment (Nm)")
        axs[2].grid(True)
        axs[2].legend()

        # 4. 曲率图
        axs[3].plot(phi.x_values, phi.y_values, label="Curvature Phi", color="tab:green")
        axs[3].set_xlabel("Position x (mm)")
        axs[3].set_ylabel("Phi")
        axs[3].grid(True)
        axs[3].legend()

        fig1.suptitle("Beam Simulation Results - Internal Forces")
        fig1.tight_layout()

        # 窗口 2: 材料拉压与 Glue Joint 剪应力对比图
        fig2, (ax2_1, ax2_2) = plt.subplots(2, 1, figsize=(9, 8), sharex=True)

        # 1. 顶/底拉压应力包络线及极限
        ax2_1.plot(top_tensile.x_values, top_tensile.y_values, label="Top Tensile Force", color="tab:purple", linewidth=1.5)
        ax2_1.plot(bottom_tensile.x_values, bottom_tensile.y_values, label="Bottom Tensile Force", color="tab:red", linewidth=1.5)

        ax2_1.axhline(y=TENSION_LIMIT, color='red', linestyle='--', linewidth=1.5, label=f"Tension Limit ({TENSION_LIMIT})")
        ax2_1.axhline(y=COMPRESSION_LIMIT, color='blue', linestyle='--', linewidth=1.5, label=f"Compression Limit ({COMPRESSION_LIMIT})")

        ax2_1.set_ylabel("Tensile Force / Stress")
        ax2_1.set_title("Beam Tensile Envelope & Material Limits")
        ax2_1.grid(True)
        ax2_1.legend(loc="upper right")

        # 2. 各 Glue Tab 剪应力曲线及极限
        for idx, glue_diagram in enumerate(glue_shears):
            y_height = beam.cross_section.horizontal_glue_joints[idx]
            ax2_2.plot(glue_diagram.x_values, glue_diagram.y_values, label=f"Glue Joint at y={y_height} mm")

        ax2_2.axhline(y=GLUE_SHEAR_LIMIT, color='darkred', linestyle='--', linewidth=1.5, label=f"Glue Shear Limit ({GLUE_SHEAR_LIMIT} MPa)")

        ax2_2.set_xlabel("Position x (mm)")
        ax2_2.set_ylabel("Glue Shear Stress (MPa)")
        ax2_2.set_title("Glue Joint Shear Stress Envelope")
        ax2_2.grid(True)
        ax2_2.legend(loc="upper right")

        fig2.tight_layout()

        # 同时显示两个窗口
        plt.show()

    else:
        print("Unknown command, type 'help' for help")

while True:
    try:
        user_input = input("> ")
        parse_command(user_input)
    except (EOFError, KeyboardInterrupt):
        break
    except Exception as e:
        print(f"error: {e}")