
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
import os

# --- Simulation Parameters ---
E_MAX_WH = 22.0
P_IDLE = 0.25
C_TH = 120.0
R_TH = 3.2
T_AMB = 25.0

# New Color Profile: Light Mode
COLOR_SOC = '#3C9Bc9'    # Blue
COLOR_TEMP = '#FC757B'   # Coral
COLOR_SCREEN = '#F88455' # Orange
COLOR_PROC = '#76CBB4'   # Teal
COLOR_MODEM = '#FDCA93'  # Peach
COLOR_GRID = '#f1f5f9'   # Soft gray grid

def get_live_data(duration_h=4, dt_s=60):
    t_s = np.arange(0, duration_h * 3600, dt_s)
    t_h = t_s / 3600
    
    # Power profile: Idle -> Video -> Game -> Nav
    # (0-1h) (1-2h) (2-3h) (3-4h)
    p_sys = np.zeros_like(t_h)
    p_sys[t_h < 1] = 0.5  # Idle
    p_sys[(t_h >= 1) & (t_h < 2)] = 1.8  # Video
    p_sys[(t_h >= 2) & (t_h < 3)] = 4.5  # Gaming
    p_sys[t_h >= 3] = 2.5  # Navigation
    
    # Add some noise
    p_sys += np.random.normal(0, 0.1 * p_sys, len(p_sys))
    p_sys = np.maximum(p_sys, 0.1)
    
    # Simulate SOC
    soc = np.zeros_like(t_h)
    soc[0] = 1.0
    for i in range(len(t_h)-1):
        p_bat = p_sys[i] + P_IDLE
        soc[i+1] = soc[i] - (p_bat / E_MAX_WH) * (dt_s/3600)
    
    # Simulate Temp
    temp = np.zeros_like(t_h)
    temp[0] = T_AMB
    for i in range(len(t_h)-1):
        p_bat = p_sys[i] + P_IDLE
        dTdt = (p_bat / C_TH) - (temp[i] - T_AMB) / (R_TH * C_TH)
        temp[i+1] = temp[i] + dTdt * dt_s
        
    return t_h, p_sys, soc, temp

def make_soc_temp_gif(out_path):
    t_h, p_sys, soc, temp = get_live_data()
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
    fig.patch.set_facecolor('#ffffff')
    plt.subplots_adjust(hspace=0.3)
    
    # Grid and Spine styling
    for ax in [ax1, ax2]:
        ax.set_facecolor('#ffffff')
        ax.grid(True, color=COLOR_GRID, linestyle='-', linewidth=1)
        for spine in ax.spines.values():
            spine.set_color('#e2e8f0')

    # SOC Plot
    ax1.set_ylim(0, 105)
    ax1.set_ylabel("SOC (%)", fontname='Arial', fontweight='bold')
    ax1.grid(True, alpha=0.2)
    line_soc, = ax1.plot([], [], color=COLOR_SOC, linewidth=3, label='Battery Level')
    ax1.legend(loc='upper right', frameon=False)
    
    # Temp Plot
    ax2.set_ylim(20, 55)
    ax2.set_ylabel("Temp (°C)", fontname='Arial', fontweight='bold')
    ax2.set_xlabel("Time (hours)", fontname='Arial', fontweight='bold')
    ax2.grid(True, alpha=0.2)
    line_temp, = ax2.plot([], [], color=COLOR_TEMP, linewidth=3, label='Device Heat')
    ax2.legend(loc='upper right', frameon=False)
    
    def init():
        line_soc.set_data([], [])
        line_temp.set_data([], [])
        return line_soc, line_temp

    def update(frame):
        x = t_h[:frame]
        y_soc = soc[:frame] * 100
        y_temp = temp[:frame]
        line_soc.set_data(x, y_soc)
        line_temp.set_data(x, y_temp)
        ax1.set_xlim(0, 4)
        return line_soc, line_temp

    ani = FuncAnimation(fig, update, frames=np.arange(0, len(t_h), 5), init_func=init, blit=True)
    ani.save(out_path, writer=PillowWriter(fps=15))
    plt.close()

def make_power_gif(out_path):
    t_h, p_sys, soc, temp = get_live_data()
    
    # Create component stacks
    p_cpu = p_sys * 0.4
    p_screen = p_sys * 0.35 + 0.5
    p_modem = p_sys * 0.25
    
    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_facecolor('#ffffff')
    ax.set_facecolor('#ffffff')

    # Using stackplot animation is tricky, we'll use fill_between
    def update(frame):
        ax.clear()
        ax.set_facecolor('#ffffff')
        ax.grid(True, color=COLOR_GRID, linestyle='-', linewidth=1)
        for spine in ax.spines.values():
            spine.set_color('#e2e8f0')
        ax.set_ylim(0, 7)
        ax.set_xlim(0, 4)
        ax.set_ylabel("Power Draw (W)", fontweight='bold')
        ax.set_xlabel("Time (hours)", fontweight='bold')
        x = t_h[:frame]
        ax.fill_between(x, 0, p_modem[:frame], color=COLOR_MODEM, alpha=0.9, label='Modem')
        ax.fill_between(x, p_modem[:frame], p_modem[:frame]+p_screen[:frame], color=COLOR_SCREEN, alpha=0.9, label='Display')
        ax.fill_between(x, p_modem[:frame]+p_screen[:frame], p_modem[:frame]+p_screen[:frame]+p_cpu[:frame], color=COLOR_PROC, alpha=0.9, label='Processor')
        ax.legend(loc='upper right', ncol=3, frameon=False)
        ax.set_title("Real-time Hardware Power Consumption", fontweight='bold')
        return [] # Return empty list as we are not using blit=True here

    ani = FuncAnimation(fig, update, frames=np.arange(1, len(t_h), 10))
    ani.save(out_path, writer=PillowWriter(fps=15))
    plt.close()

def make_stochastic_gif(out_path):
    duration_h = 4
    dt_s = 60
    t_h = np.arange(0, duration_h * 3600, dt_s) / 3600
    
    # 20 independent runs
    runs = []
    for _ in range(20):
        _, _, run_soc, _ = get_live_data(duration_h, dt_s)
        runs.append(run_soc)
    
    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_facecolor('#ffffff')
    ax.set_facecolor('#ffffff')
    ax.grid(True, color=COLOR_GRID, linestyle='-', linewidth=1)
    for spine in ax.spines.values():
        spine.set_color('#e2e8f0')

    ax.set_ylim(0, 105)
    ax.set_xlim(0, 4)
    ax.set_ylabel("SOC (%)", fontweight='bold')
    ax.set_xlabel("Time (hours)", fontweight='bold')
    ax.set_title("Stochastic Simulation: 95% Confidence Bounds", fontweight='bold')
    
    lines = [ax.plot([], [], color=COLOR_PROC, alpha=0.1, linewidth=1)[0] for _ in range(20)]
    mean_line, = ax.plot([], [], color=COLOR_SOC, linewidth=4, label='Mean Trend')
    
    def init():
        for l in lines: l.set_data([], [])
        mean_line.set_data([], [])
        return lines + [mean_line]

    def update(frame):
        x = t_h[:frame]
        all_socs = []
        for i, l in enumerate(lines):
            y = runs[i][:frame] * 100
            l.set_data(x, y)
            all_socs.append(y)
        
        if frame > 0:
            mean_y = np.mean([r[:frame] for r in runs], axis=0) * 100
            mean_line.set_data(x, mean_y)
            
        return lines + [mean_line]

    ani = FuncAnimation(fig, update, frames=np.arange(0, len(t_h), 5), init_func=init, blit=True)
    ani.save(out_path, writer=PillowWriter(fps=15))
    plt.close()

if __name__ == "__main__":
    img_dir = "/Users/xiaruize/Documents/MCM/website/img"
    os.makedirs(img_dir, exist_ok=True)
    
    print("Generating live_soc_temp.gif...")
    make_soc_temp_gif(os.path.join(img_dir, "live_soc_temp.gif"))
    
    print("Generating live_power.gif...")
    make_power_gif(os.path.join(img_dir, "live_power.gif"))
    
    print("Generating live_monte_carlo.gif...")
    make_stochastic_gif(os.path.join(img_dir, "live_monte_carlo.gif"))
    
    print("Done!")
