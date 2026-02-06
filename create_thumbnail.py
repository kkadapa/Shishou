
import PIL.Image
import PIL.ImageFilter

def create_thumbnail(input_path, output_path, target_ratio=(3, 2), target_width=1500):
    img = PIL.Image.open(input_path)
    
    # Calculate target dimensions
    target_height = int(target_width * target_ratio[1] / target_ratio[0])
    target_size = (target_width, target_height)
    
    # Create background: Blurred version of the original image
    # Resize original to cover the target size
    bg_scale = max(target_width / img.width, target_height / img.height)
    bg_size = (int(img.width * bg_scale), int(img.height * bg_scale))
    background = img.resize(bg_size, PIL.Image.Resampling.LANCZOS)
    
    # Center crop the background to target size
    left = (background.width - target_width) / 2
    top = (background.height - target_height) / 2
    background = background.crop((left, top, left + target_width, top + target_height))
    
    # Apply blur
    background = background.filter(PIL.ImageFilter.GaussianBlur(radius=20))
    
    # Resize foreground image to fit inside target size with some padding
    padding = 50
    max_fg_width = target_width - (padding * 2)
    max_fg_height = target_height - (padding * 2)
    
    fg_scale = min(max_fg_width / img.width, max_fg_height / img.height)
    fg_size = (int(img.width * fg_scale), int(img.height * fg_scale))
    foreground = img.resize(fg_size, PIL.Image.Resampling.LANCZOS)
    
    # Paste foreground onto background (centered)
    fg_x = (target_width - fg_size[0]) // 2
    fg_y = (target_height - fg_size[1]) // 2
    
    # Add a simple drop shadow (optional, but looks nice)
    # Creating a black rectangle for shadow
    shadow = PIL.Image.new('RGBA', fg_size, (0, 0, 0, 100))
    # Paste partial shadow
    background.paste(shadow, (fg_x + 10, fg_y + 10), shadow)
    
    background.paste(foreground, (fg_x, fg_y))
    
    # Save
    background.convert('RGB').save(output_path, quality=90)
    print(f"Created {output_path} ({target_width}x{target_height})")

if __name__ == "__main__":
    create_thumbnail('Shishou-demo.png', 'Shishou-thumbnail.jpg')
