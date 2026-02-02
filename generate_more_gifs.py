
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
import os

# --- Core Simulation Engine (Same as main script) ---
E_MAX_WH = 22.0 # Standard ~5000mAh battery
P_IDLE = 0.25
C_TH = 120.0
R_TH = 3.2
T_AMB_STD = 25.0

# New Color Profile: Light Mode
COLOR_SOC = '#3C9Bc9'    # Blue
COLOR_TEMP = '#FC757B'   # Coral
COLOR_SCREEN = '#F88455' # Orange
COLOR_PROC = '#76CBB4'   # Teal
COLOR_MODEM = '#FDCA93'  # Peach
COLOR_GRID = '#f1f5f9'   # Soft gray grid

def simulate_scenario(duration_h=6, dt_s=60, p_profile=None, t_amb=25.0, e_max=22.0):
    t_s = np.arange(0, duration_h * 3600, dt_s)
    t_h = t_s / 3600
    
    if p_profile is None:
        p_sys = np.full_like(t_h, 2.0)
    else:
        p_sys = p_profile(t_h)
        
    soc = np.zeros_like(t_h)
    temp = np.zeros_like(t_h)
    soc[0] = 1.0
    temp[0] = t_amb
    
    for i in range(len(t_h)-1):
        p_bat = p_sys[i] + P_IDLE
        # SOC decay
        soc[i+1] = max(0, soc[i] - (p_bat / e_max) * (dt_s/3600))
        # Thermal evolution
        dTdt = (p_bat / C_TH) - (temp[i] - t_amb) / (R_TH * C_TH)
        temp[i+1] = temp[i] + dTdt * dt_s
        
        # Stop if battery dead
        if soc[i+1] <= 0:
            soc[i+1:] = 0
            # Temp slowly returns to ambient
            for j in range(i+1, len(t_h)-1):
                dTdt = - (temp[j] - t_amb) / (R_TH * C_TH)
                temp[j+1] = temp[j] + dTdt * dt_s
            break
            
    return t_h, p_sys, soc, temp

# --- Specific Scenarios ---

def make_low_power_vs_normal_gif(out_path):
    def normal_profile(t):
        p = np.full_like(t, 2.5) # General high usage
        p[t > 2] = 4.5 # Heavy gaming
        return p
        
    def low_power_profile(t):
        p = np.full_like(t, 1.5) # Throttled
        p[t > 2] = 2.0 # Throttled gaming
        return p

    t_h, p1, s1, t1 = simulate_scenario(duration_h=8, p_profile=normal_profile)
    _, p2, s2, t2 = simulate_scenario(duration_h=8, p_profile=low_power_profile)
    
    fig, ax = plt.subplots(figsize=(8, 5))
    fig.patch.set_facecolor('#ffffff')
    ax.set_facecolor('#ffffff')
    ax.grid(True, color=COLOR_GRID, linestyle='-', linewidth=1)
    for spine in ax.spines.values():
        spine.set_color('#e2e8f0')

    ax.set_ylim(0, 105)
    ax.set_xlim(0, 8)
    ax.set_ylabel("Battery Percentage (%)", fontweight='bold')
    ax.set_xlabel("Time (hours)", fontweight='bold')
    ax.set_title("Standard vs. Low Power Mode", fontweight='bold')
    
    line1, = ax.plot([], [], color=COLOR_TEMP, linewidth=3, label='Normal Mode')
    line2, = ax.plot([], [], color=COLOR_SOC, linewidth=3, label='Power Saving')
    ax.legend()

    def update(frame):
        x = t_h[:frame]
        line1.set_data(x, s1[:frame]*100)
        line2.set_data(x, s2[:frame]*100)
        return line1, line2

    ani = FuncAnimation(fig, update, frames=np.arange(0, len(t_h), 10), blit=True)
    ani.save(out_path, writer=PillowWriter(fps=15))
    plt.close()

def make_thermal_stress_gif(out_path):
    # Same intensive profile for both
    def heavy_profile(t): return np.full_like(t, 3.5)
    
    t_h, p1, s1, t1 = simulate_scenario(duration_h=5, p_profile=heavy_profile, t_amb=25.0)
    _, p2, s2, t2 = simulate_scenario(duration_h=5, p_profile=heavy_profile, t_amb=40.0)
    
    fig, ax = plt.subplots(figsize=(8, 5))
    fig.patch.set_facecolor('#ffffff')
    ax.set_facecolor('#ffffff')
    ax.grid(True, color=COLOR_GRID, linestyle='-', linewidth=1)
    for spine in ax.spines.values():
        spine.set_color('#e2e8f0')

    ax.set_ylim(20, 65)
    ax.set_xlim(0, 5)
    ax.set_ylabel("Internal Temperature (°C)", fontweight='bold')
    ax.set_xlabel("Time (hours)", fontweight='bold')
    ax.set_title("Thermal Stress: Ambient 25°C vs. 40°C", fontweight='bold')
    
    line1, = ax.plot([], [], color=COLOR_PROC, linewidth=3, label='Room Temp (25°C)')
    line2, = ax.plot([], [], color=COLOR_SOC, linewidth=3, label='Extreme Heat (40°C)')
    ax.axhline(50, color=COLOR_TEMP, linestyle='--', alpha=0.5, label='Throttling Threshold')
    ax.legend(loc='lower right')

    def update(frame):
        x = t_h[:frame]
        line1.set_data(x, t1[:frame])
        line2.set_data(x, t2[:frame])
        return line1, line2

    ani = FuncAnimation(fig, update, frames=np.arange(0, len(t_h), 10), blit=True)
    ani.save(out_path, writer=PillowWriter(fps=15))
    plt.close()

def make_gaming_marathon_gif(out_path):
    # Constant high drain
    def gaming_profile(t): return np.full_like(t, 5.5)
    
    t_h, p, s, t = simulate_scenario(duration_h=5, p_profile=gaming_profile)
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
    plt.subplots_adjust(hspace=0.3)
    
    ax1.set_ylim(0, 105)
    ax1.set_ylabel("SOC (%)", fontweight='bold')
    ax1.set_title("Gaming Marathon (Constant 5.5W)", fontweight='bold')
    line_soc, = ax1.plot([], [], color=COLOR_SOC, linewidth=3)
    
    ax2.set_ylim(25, 55)
    ax2.set_ylabel("Temp (°C)", fontweight='bold')
    ax2.set_xlabel("Time (hours)", fontweight='bold')
    line_temp, = ax2.plot([], [], color=COLOR_TEMP, linewidth=3)

    def update(frame):
        x = t_h[:frame]
        line_soc.set_data(x, s[:frame]*100)
        line_temp.set_data(x, t[:frame])
        ax1.set_xlim(0, 4)
        return line_soc, line_temp

    ani = FuncAnimation(fig, update, frames=np.arange(0, len(t_h), 10), blit=True)
    ani.save(out_path, writer=PillowWriter(fps=15))
    plt.close()

if __name__ == "__main__":
    img_dir = "/Users/xiaruize/Documents/MCM/website/img"
    os.makedirs(img_dir, exist_ok=True)
    
    print("Generating live_low_power.gif...")
    make_low_power_vs_normal_gif(os.path.join(img_dir, "live_low_power.gif"))
    
    print("Generating live_thermal_stress.gif...")
    make_thermal_stress_gif(os.path.join(img_dir, "live_thermal_stress.gif"))
    
    print("Generating live_gaming_marathon.gif...")
    make_gaming_marathon_gif(os.path.join(img_dir, "live_gaming_marathon.gif"))
    
    print("All tasks complete!")
