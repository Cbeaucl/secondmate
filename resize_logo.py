import os
from PIL import Image

input_path = "SECONDMATE_LOGO.png"
output_path = "src/assets/logo.png"

def resize_image():
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found")
        return
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with Image.open(input_path) as img:
        # Resize to a reasonable width for a web application logo
        target_width = 400
        wpercent = (target_width / float(img.size[0]))
        target_height = int((float(img.size[1]) * float(wpercent)))
        
        # Use LANCZOS for high-quality downsampling
        img_resized = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        # Save as optimized PNG
        img_resized.save(output_path, "PNG", optimize=True)
        print(f"Successfully resized and saved to {output_path}")

if __name__ == "__main__":
    resize_image()
