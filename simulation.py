import matplotlib.pyplot as plt
from beam import *
from cross_section import *

beam = Beam(1200, 4000)

shear_max = Diagram(beam.simulation_list)
shear_min = Diagram(beam.simulation_list)
moment = Diagram(beam.simulation_list)
phi = Diagram(beam.simulation_list)

train_len = 960

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
    global beam, shear_max, shear_min, phi, moment, train_len

    loads = generate_load(0.1) # lightest train weighs 100N

    for i in range(beam.length + train_len + 1):
        beam.clear_force()
        for j in loads:
            beam.add_force(j)

        beam.solve()

        shear_max.update_y_values(elementwise_max(beam.shear.y_values, shear_max.y_values))
        shear_min.update_y_values(elementwise_min(beam.shear.y_values, shear_min.y_values))
        moment.update_y_values(max_abs_list(beam.moment.y_values, moment.y_values))
        phi.update_y_values(max_abs_list(beam.phi.y_values, phi.y_values))

        move_loads(1, loads)

def parse_command(command: str):
    global shear_max, shear_min, moment, phi
    
    tokens = command.strip().split()
    if not tokens:
        return

    cmd = tokens[0].lower()
    args = tokens[1:]

    if cmd == "help":
        print("Command list: ")
        print("  help: show command list")
        print("  add_rect x1 x2 y1 y2: Add rectangle cross section (xmin xmax ymin ymax)")
        print("  clear_rect: clear all cross sections")
        print("  run: run train through and plot graphs")

    elif cmd == "add_rect":
        x1, x2, y1, y2 = map(float, args)
        rect = Rectangle((x1, x2), (y1, y2))
        beam.cross_section.add_rectangle(rect)

    elif cmd == "clear_rect":
        beam.cross_section.clear_rect()

    elif cmd == "run":
        beam.cross_section.solve()

        shear_max = Diagram(beam.simulation_list)
        shear_min = Diagram(beam.simulation_list)
        moment = Diagram(beam.simulation_list)
        phi = Diagram(beam.simulation_list)

        run_train()

        fig, axs = plt.subplots(4, 1, figsize=(9, 10), sharex=True)

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
        axs[2].set_ylabel("Moment (Nm)")
        axs[2].grid(True)
        axs[2].legend()

        # 4. 曲率图
        axs[3].plot(phi.x_values, phi.y_values, label="Curvature Phi", color="tab:green")
        axs[3].set_xlabel("Position x (mm)")
        axs[3].set_ylabel("Phi")
        axs[3].grid(True)
        axs[3].legend()

        plt.suptitle("Beam Simulation Results")
        plt.tight_layout()
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