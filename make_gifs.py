from PIL import Image
import os

def create_gif(image_paths, output_path, duration=1500):
    images = []
    for path in image_paths:
        if os.path.exists(path):
            img = Image.open(path)
            # Ensure index color mode for GIF
            img = img.convert("RGBA")
            # Create a white background if there's transparency
            background = Image.new("RGBA", img.size, (255, 255, 255))
            composite = Image.alpha_composite(background, img)
            images.append(composite.convert("RGB"))
    
    if images:
        images[0].save(
            output_path,
            save_all=True,
            append_images=images[1:],
            duration=duration,
            loop=0
        )
        print(f"Created {output_path}")

img_dir = "/Users/xiaruize/Documents/MCM/MCM_ICM_02021712/img"
web_img_dir = "/Users/xiaruize/Documents/MCM/website/img"

# 1. Scenario Lifecycle
scenarios = [
    "Scenario_Idle_Standby_with_SOC.png",
    "Scenario_Social_Browsing_with_SOC.png",
    "Scenario_Video_Streaming_with_SOC.png",
    "Scenario_Gaming_with_SOC.png",
    "Scenario_Navigation_with_SOC.png"
]
create_gif([os.path.join(img_dir, s) for s in scenarios], os.path.join(web_img_dir, "scenarios_lifecycle.gif"))

# 2. Sensitivity Tornadoes
tornadoes = [
    "sensitivity_tte_tornado_Idle.png",
    "sensitivity_tte_tornado_Browsing.png",
    "sensitivity_tte_tornado_Streaming.png",
    "sensitivity_tte_tornado_Gaming.png",
    "sensitivity_tte_tornado_Navigation.png"
]
create_gif([os.path.join(img_dir, t) for t in tornadoes], os.path.join(web_img_dir, "sensitivity_cycle.gif"))

# 3. Realworld Analysis
realworld = [
    "fig_realworld_Idle_Standby.png",
    "fig_realworld_Social_Browsing.png",
    "fig_realworld_Video_Streaming.png",
    "fig_realworld_Gaming.png",
    "fig_realworld_Navigation.png"
]
create_gif([os.path.join(img_dir, r) for r in realworld], os.path.join(web_img_dir, "realworld_cycle.gif"))
