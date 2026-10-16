import os
from PIL import Image, ImageDraw, ImageFont

def create_mock_ui():
    img = Image.new('RGB', (1920, 1080), color=(250, 250, 252))
    draw = ImageDraw.Draw(img)
    
    # Sidebar
    draw.rectangle([0, 0, 250, 1080], fill=(255, 255, 255))
    draw.line([250, 0, 250, 1080], fill=(230, 230, 230), width=2)
    
    # Sidebar items
    for i in range(5):
        draw.rectangle([20, 100 + (i*60), 230, 140 + (i*60)], fill=(240, 245, 255) if i==0 else (255,255,255))
    
    # Header
    draw.rectangle([250, 0, 1920, 80], fill=(255, 255, 255))
    draw.line([250, 80, 1920, 80], fill=(230, 230, 230), width=2)
    
    # Dashboard Cards
    draw.rectangle([300, 120, 700, 300], fill=(255, 255, 255), outline=(220, 220, 220), width=2)
    draw.rectangle([730, 120, 1130, 300], fill=(255, 255, 255), outline=(220, 220, 220), width=2)
    draw.rectangle([1160, 120, 1870, 300], fill=(255, 255, 255), outline=(220, 220, 220), width=2)
    
    # Main Chart Area
    draw.rectangle([300, 340, 1870, 1000], fill=(255, 255, 255), outline=(220, 220, 220), width=2)
    
    # Fake Chart Line
    points = [(350, 800), (500, 700), (700, 750), (900, 500), (1100, 600), (1300, 400), (1500, 450), (1800, 380)]
    draw.line(points, fill=(0, 113, 227), width=8, joint="curve")
    
    out_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "input", "ui_assets", "mock_saas_dashboard.png")
    img.save(out_path)
    print(f"Created {out_path}")

if __name__ == "__main__":
    create_mock_ui()
