from PIL import Image
import os

png_path = r"C:\Users\Admin\.gemini\antigravity\brain\8b266787-39ad-4078-b84b-c3bce56ecec2\pms_logo_png_1773546844964.png"
ico_path = r"C:\Users\Admin\ProjectManegements\pms_icon.ico"

if os.path.exists(png_path):
    img = Image.open(png_path)
    # Define common icon sizes
    icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(ico_path, sizes=icon_sizes)
    print(f"Icon created at {ico_path}")
else:
    print(f"Error: PNG not found at {png_path}")
