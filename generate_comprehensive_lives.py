import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
import os

# --- Parameters from redo_plots_figures/real_world_sim.py ---
E_MAX_WH = 22.0
C_TH = 2000.0
R_TH = 2.2
T_AMB = 25.0
T_REF = 25.0
P_CPU_STATIC = 0.40
K_CPU_BASE = 5.0
ALPHA_CPU_T = 0.002
GAMMA_CPU = 2.0

scenarios_params = {
    "Idle":      {"u_s":0, "b":0.0, "U":0.05, "Rdl":0.10, "Rul":0.05, "Srx":0.20, "Stx":0.20, "f_g":0.01},
    "Browsing":  {"u_s":1, "b":0.4, "U":0.80, "Rdl":5.00, "Rul":0.50, "Srx":0.30, "Stx":0.30, "f_g":0.02},
    "Video":     {"u_s":1, "b":0.6, "U":1.00, "Rdl":6.00, "Rul":0.50, "Srx":0.30, "Stx":0.30, "f_g":0.02},
    "Gaming":    {"u_s":1, "b":0.7, "U":1.605, "Rdl":1.00, "Rul":0.20, "Srx":0.25, "Stx":0.25, "f_g":0.01},
    "Navigation":{"u_s":1, "b":0.6, "U":0.90, "Rdl":2.00, "Rul":0.20, "Srx":0.35, "Stx":0.35, "f_g":0.80},
}

COLOR_SOC = '#3C9Bc9'
COLOR_TEMP = '#FC757B'
COLOR_SCREEN = '#F88455'
COLOR_PROC = '#76CBB4'
COLOR_MODEM = '#FDCA93'
COLOR_GRID = '#f1f5f9'

def get_scenario_power(s_name, T_curr):
    s = scenarios_params[s_name]
    P_screen = s["u_s"] * (200.0 * 0.007 * s["b"] + 0.20)
    P_proc = P_CPU_STATIC + K_CPU_BASE * (s["U"]**GAMMA_CPU) * (1 + ALPHA_CPU_T * (T_curr - T_REF))
    P_modem = 0.40 + (s["Rdl"]*0.05 + s["Rul"]*0.08) + (s["Srx"]*0.25 + s["Stx"]*0.25)
    P_gps = (0.2 + 0.063 * s["f_g"]) if s["u_s"] > 0 else 0
    P_misc = 0.25 + 0.1
    return P_screen + P_proc + P_modem + P_gps + P_misc

def simulate_scenario_fixed(s_name, duration_h=12):
    dt = 60
    steps = int(duration_h * 60)
    t_h = np.linspace(0, duration_h, steps)
    soc = np.zeros(steps)
    temp = np.zeros(steps)
    soc[0] = 1.0
    temp[0] = T_AMB
    for i in range(steps-1):
        p = get_scenario_power(s_name, temp[i])
        soc[i+1] = max(0, soc[i] - (p / E_MAX_WH) * (1/60))
        dT = (p - (temp[i] - T_AMB)/R_TH) * (60 / C_TH)
        temp[i+1] = temp[i] + dT
        if soc[i+1] <= 0:
            t_h = t_h[:i+2]; soc = soc[:i+2]; temp = temp[:i+2]
            break
    return t_h, soc, temp

def make_scenario_gif(s_name, out_path):
    t_h, soc, temp = simulate_scenario_fixed(s_name)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6, 6))
    fig.patch.set_facecolor('#ffffff')
    plt.subplots_adjust(hspace=0.45)
    for ax in [ax1, ax2]:
        ax.set_facecolor('#ffffff')
        ax.grid(True, color=COLOR_GRID, linestyle='-', linewidth=1)
        for spine in ax.spines.values(): spine.set_color('#e2e8f0')
    ax1.set_xlim(0, 12); ax1.set_ylim(0, 105)
    ax1.set_title(f"SOC Decay: {s_name}", fontweight='bold', color=COLOR_SOC)
    line_soc, = ax1.plot([], [], color=COLOR_SOC, lw=4)
    ax2.set_xlim(0, 12); ax2.set_ylim(20, 50)
    ax2.set_title(f"Thermal Profile (°C)", fontweight='bold', color=COLOR_TEMP)
    line_temp, = ax2.plot([], [], color=COLOR_TEMP, lw=4)
    def update(frame):
        idx = frame * 10
        if idx >= len(t_h): idx = len(t_h) - 1
        line_soc.set_data(t_h[:idx], soc[:idx]*100)
        line_temp.set_data(t_h[:idx], temp[:idx])
        return [line_soc, line_temp]
    ani = FuncAnimation(fig, update, frames=len(t_h)//10 + 15, blit=True)
    ani.save(out_path, writer=PillowWriter(fps=25))
    plt.close()

def make_sweep_gif(title, x_label, y_label, x_vals, y_func, color, out_path, ylim=None):
    fig, ax = plt.subplots(figsize=(6, 4))
    fig.patch.set_facecolor('#ffffff')
    ax.set_facecolor('#ffffff')
    ax.grid(True, color=COLOR_GRID, linestyle='-', linewidth=1)
    for spine in ax.spines.values(): spine.set_color('#e2e8f0')
    ax.set_xlim(min(x_vals), max(x_vals))
    y_vals = [y_func(x) for x in x_vals]
    ax.set_ylim(0, ylim or max(y_vals)*1.2)
    ax.set_title(title, fontweight='bold', color=color)
    ax.set_xlabel(x_label); ax.set_ylabel(y_label)
    line, = ax.plot([], [], color=color, lw=4)
    def update(frame):
        curr_idx = min(frame, len(x_vals)-1)
        line.set_data(x_vals[:curr_idx], y_vals[:curr_idx])
        return [line]
    ani = FuncAnimation(fig, update, frames=len(x_vals)+10, blit=True)
    ani.save(out_path, writer=PillowWriter(fps=20))
    plt.close()

def make_stress_comparison_gif(out_path):
    modes = ["Browsing", "Navigation", "Gaming"]
    colors = [COLOR_PROC, COLOR_SCREEN, COLOR_TEMP]
    sims = []
    for m in modes:
        t, s, temp = simulate_scenario_fixed(m, duration_h=6)
        sims.append((t, s, temp))
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    fig.patch.set_facecolor('#ffffff')
    plt.subplots_adjust(hspace=0.4)
    for ax in [ax1, ax2]:
        ax.set_facecolor('#ffffff')
        ax.grid(True, color=COLOR_GRID, linestyle='-', alpha=0.5)
        ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    ax1.set_title("SOC Decay Comparison", fontweight='bold')
    ax1.set_ylabel("SOC %"); ax1.set_xlim(0, 6); ax1.set_ylim(0, 105)
    ax2.set_title("Thermal Response Comparison", fontweight='bold')
    ax2.set_ylabel("Temp °C"); ax2.set_xlabel("Hours"); ax2.set_xlim(0, 6); ax2.set_ylim(20, 55)
    lines_soc = [ax1.plot([], [], label=m, color=c, lw=3)[0] for m, c in zip(modes, colors)]
    lines_temp = [ax2.plot([], [], label=m, color=c, lw=3)[0] for m, c in zip(modes, colors)]
    ax1.legend(loc='lower left', fontsize=9, frameon=False)
    def update(frame):
        idx = frame * 10
        for i, (t, s, temp) in enumerate(sims):
            if idx < len(t):
                lines_soc[i].set_data(t[:idx], s[:idx]*100)
                lines_temp[i].set_data(t[:idx], temp[:idx])
            else:
                lines_soc[i].set_data(t, s*100)
                lines_temp[i].set_data(t, temp)
        return lines_soc + lines_temp
    max_len = max(len(t) for t, s, temp in sims)
    ani = FuncAnimation(fig, update, frames=max_len//10 + 20, blit=True)
    ani.save(out_path, writer=PillowWriter(fps=20))
    plt.close()

def make_monte_carlo_gif(out_path):
    t_h = np.linspace(0, 8, 480)
    fig, ax = plt.subplots(figsize=(6, 4))
    fig.patch.set_facecolor('#ffffff')
    ax.set_facecolor('#ffffff'); ax.grid(True, color=COLOR_GRID)
    ax.set_title("Confidence Intervals", fontweight='bold', color=COLOR_SOC)
    ax.set_xlim(0, 8); ax.set_ylim(0, 105)
    ax.set_ylabel("SOC %"); ax.set_xlabel("Time (Hours)")
    base_rate = 12.0
    lines = []
    for _ in range(10):
        noise = np.random.normal(1.0, 0.15)
        l, = ax.plot([], [], color=COLOR_SOC, alpha=0.15, lw=1)
        lines.append((l, noise))
    main_line, = ax.plot([], [], color=COLOR_SOC, lw=4)
    def update(frame):
        x = t_h[:frame]
        for l, n in lines: l.set_data(x, 100 - x * base_rate * n)
        main_line.set_data(x, 100 - x * base_rate)
        return [main_line] + [l for l, _ in lines]
    ani = FuncAnimation(fig, update, frames=len(t_h)//8, blit=True)
    ani.save(out_path, writer=PillowWriter(fps=20))
    plt.close()

def make_power_breakdown_gif(out_path):
    checkpoints = [("Idle", 30), ("Browsing", 50), ("Gaming", 70), ("Video", 50), ("Idle", 30)]
    all_p_cpu, all_p_scr, all_p_mdm, all_p_misc, labels = [], [], [], [], []
    temp_sim = 35.0
    def get_comp_power(s_name):
        s_data = scenarios_params[s_name]
        p_scr = s_data["u_s"] * (200.0 * 0.007 * s_data["b"] + 0.20)
        p_cpu = P_CPU_STATIC + K_CPU_BASE * (s_data["U"]**GAMMA_CPU) * (1 + ALPHA_CPU_T * (temp_sim - T_REF))
        p_mdm = 0.40 + (s_data["Rdl"]*0.05 + s_data["Rul"]*0.08) + (s_data["Srx"]*0.25 + s_data["Stx"]*0.25)
        p_misc = 0.25 + 0.1 + ((0.2 + 0.063 * s_data["f_g"]) if s_data["u_s"] > 0 else 0)
        return p_cpu, p_scr, p_mdm, p_misc
    for i in range(len(checkpoints) - 1):
        start_mode, _ = checkpoints[i]
        end_mode, dur = checkpoints[i+1]
        p_start, p_end = get_comp_power(start_mode), get_comp_power(end_mode)
        for step in range(dur):
            alpha = step / dur
            c = p_start[0] + (p_end[0] - p_start[0]) * alpha
            s = p_start[1] + (p_end[1] - p_start[1]) * alpha
            m = p_start[2] + (p_end[2] - p_start[2]) * alpha
            mi = p_start[3] + (p_end[3] - p_start[3]) * alpha
            j = np.random.normal(1.0, 0.015)
            all_p_cpu.append(c * j); all_p_scr.append(s * j); all_p_mdm.append(m * j); all_p_misc.append(mi * j)
            if alpha < 0.2: labels.append(f"MODE: {start_mode}")
            elif alpha > 0.8: labels.append(f"MODE: {end_mode}")
            else: labels.append(f"SWITCHING TO {end_mode}...")
    for _ in range(40):
        all_p_cpu.append(all_p_cpu[-1]); all_p_scr.append(all_p_scr[-1]); all_p_mdm.append(all_p_mdm[-1]); all_p_misc.append(all_p_misc[-1]); labels.append(labels[-1])
    fig, ax = plt.subplots(figsize=(8, 5))
    fig.patch.set_facecolor('#ffffff')
    total_frames = len(all_p_cpu); t = np.arange(total_frames)
    def update(frame):
        ax.clear(); ax.set_facecolor('#ffffff'); ax.set_xlim(0, total_frames); ax.set_ylim(0, 20)
        ax.grid(True, color='#f1f5f9', axis='y', linestyle='-', alpha=0.5)
        ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
        curr_slice = slice(0, frame + 1); x = t[curr_slice]
        ax.stackplot(x, all_p_cpu[curr_slice], all_p_scr[curr_slice], all_p_mdm[curr_slice], all_p_misc[curr_slice],
                    labels=['Processor', 'Screen', 'Modem', 'Misc / GPS'], colors=[COLOR_PROC, COLOR_SCREEN, COLOR_MODEM, '#cbd5e1'], alpha=0.9)
        curr_label = labels[frame]
        ax.text(total_frames/2, 19.1, curr_label.upper(), ha='center', va='center', fontsize=11, fontweight='black', color='#3C9Bc9', zorder=11, bbox=dict(facecolor='#f8fafc', alpha=1.0, edgecolor='none', pad=8))
        ax.set_title("POWER STACK", fontweight='bold', pad=30); ax.set_ylabel("Watts"); ax.set_xlabel("Cycle Progress")
        if frame > 1: ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), frameon=False, fontsize=9)
        plt.tight_layout()
        return []
    ani = FuncAnimation(fig, update, frames=total_frames, blit=False)
    ani.save(out_path, writer=PillowWriter(fps=20))
    plt.close()

if __name__ == "__main__":
    img_dir = "/Users/xiaruize/Documents/MCM/website/img"
    os.makedirs(img_dir, exist_ok=True)
    print("Generating Comparison GIF...")
    make_stress_comparison_gif(os.path.join(img_dir, "live_soc_temp.gif"))
    print("Generating Scenarios...")
    for s in scenarios_params.keys(): make_scenario_gif(s, os.path.join(img_dir, f"live_scenario_{s.lower()}.gif"))
    print("Generating Sweeps...")
    make_sweep_gif("Display Power", "Brightness (%)", "Power (W)", np.linspace(0, 100, 50), lambda x: 200.0 * 0.007 * (x/100) + 0.20, COLOR_SCREEN, os.path.join(img_dir, "live_screen_sweep.gif"), ylim=2.0)
    make_sweep_gif("CPU Power", "Temp (°C)", "Power (W)", np.linspace(25, 65, 50), lambda T: P_CPU_STATIC + K_CPU_BASE * (1.2**2) * (1 + 0.002*(T-25)), COLOR_PROC, os.path.join(img_dir, "live_processor_sweep.gif"), ylim=12.0)
    print("Generating MC...")
    make_monte_carlo_gif(os.path.join(img_dir, "live_monte_carlo.gif"))
    print("Generating Breakdown...")
    make_power_breakdown_gif(os.path.join(img_dir, "live_power.gif"))
    print("Done!")
