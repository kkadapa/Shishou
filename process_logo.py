
import PIL.Image
import PIL.ImageFilter
import numpy as np

def process_logo(input_path, output_path, target_size=(1500, 1000)):
    # Load image
    img = PIL.Image.open(input_path).convert("RGBA")
    
    # Create target canvas
    canvas = PIL.Image.new("RGBA", target_size)
    
    # Strategy: Blur fill background
    # Resize original to cover the whole canvas (aspect fill)
    bg_scale = max(target_size[0] / img.width, target_size[1] / img.height)
    bg_new_size = (int(img.width * bg_scale), int(img.height * bg_scale))
    bg_img = img.resize(bg_new_size, PIL.Image.Resampling.LANCZOS)
    
    # Center crop background
    left = (bg_img.width - target_size[0]) // 2
    top = (bg_img.height - target_size[1]) // 2
    bg_img = bg_img.crop((left, top, left + target_size[0], top + target_size[1]))
    
    # Heavy blur and darken for background
    bg_img = bg_img.filter(PIL.ImageFilter.GaussianBlur(radius=50))
    # Darken overlay
    dark_overlay = PIL.Image.new("RGBA", target_size, (0, 0, 0, 150))
    bg_img.alpha_composite(dark_overlay)
    
    # Resize logo to fit nicely in the center (keep aspect ratio, maybe 80% height)
    logo_target_h = int(target_size[1] * 0.85)
    scale = logo_target_h / img.height
    logo_new_size = (int(img.width * scale), int(img.height * scale))
    logo_img = img.resize(logo_new_size, PIL.Image.Resampling.LANCZOS)
    
    # Center logo
    x = (target_size[0] - logo_new_size[0]) // 2
    y = (target_size[1] - logo_new_size[1]) // 2
    
    # Paste logo
    bg_img.paste(logo_img, (x, y), logo_img)
    
    # Save
    bg_img.convert("RGB").save(output_path, quality=95)
    print(f"Saved processed logo to {output_path}")

if __name__ == "__main__":
    process_logo(
        '/Users/nathandrake/.gemini/antigravity/brain/127f03a5-d7c5-4b07-813b-a409696a321b/shishou_logo_v1_1770328937551.png', 
        'Shishou-demo.png'
    )
